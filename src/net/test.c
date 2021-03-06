/* Copyright (c) 2016-2017, Eder Leao Fernandes
 * All rights reserved.
 *
 * The contents of this file are subject to the license defined in
 * file 'doc/LICENSE'.
 *
 *
 * Author: Eder Leao Fernandes <e.leao@qmul.ac.uk>
 */

#include "flow_table.h"
#include "lib/util.h"
#include <uthash/utlist.h>
/* Creates a new mini flow table.
*
*  A mini flow table needs a flow
*  to be created.
*/
static void
mini_flow_table_new(struct flow_table* ft, struct flow* f)
{
  struct mini_flow_table* mft = xmalloc(sizeof(struct mini_flow_table));
  mft->flows = NULL;
  memcpy(&mft->mask, &f->mask, sizeof(mft->mask));
  HASH_ADD(hh, mft->flows, key, sizeof(struct ofl_flow_key), f);
  DL_APPEND(ft->flows, mft);
}

static void
mini_flow_table_add_flow(struct mini_flow_table* mft, struct flow* f)
{
  HASH_ADD(hh, mft->flows, key, sizeof(struct ofl_flow_key), f);
}

static void
flow_table_del_flow(struct flow_table* ft, struct mini_flow_table* mft,
                    struct flow* f)
{
  unsigned int num_flows;
  HASH_DEL(mft->flows, f);
  flow_destroy(f);
  num_flows = HASH_COUNT(mft->flows);
  if (!num_flows) {
    DL_DELETE(ft->flows, mft);
    free(mft);
  }
}

static bool
flow_table_del_expired(struct flow_table* ft, struct mini_flow_table* mft,
                       struct flow* f, uint64_t time)
{

  bool del = false;
  if (f->hard_timeout) {
    if (f->remove_at < time) {
      del = true;
    }
  } else if (f->idle_timeout) {
    uint64_t idle_remove = f->last_used + f->idle_timeout;
    if (idle_remove < time) {
      del = true;
    }
  }
  if (del) {
    flow_table_del_flow(ft, mft, f);
  }
  return del;
}

struct flow_table*
flow_table_new(uint8_t table_id)
{
  struct flow_table* ft = xmalloc(sizeof(struct flow_table));
  ft->table_id = table_id;
  ft->flows = NULL;
  return ft;
}

void
flow_table_destroy(struct flow_table* ft)
{
  struct mini_flow_table *nxt_mft, *tmp;
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    struct flow *cur_flow, *tmp;
    HASH_ITER(hh, nxt_mft->flows, cur_flow, tmp)
    {
      HASH_DEL(nxt_mft->flows, cur_flow);
      flow_destroy(cur_flow);
    }
    DL_DELETE(ft->flows, nxt_mft);
    free(nxt_mft);
  }
  free(ft);
}

struct flow*
flow_table_lookup(struct flow_table* ft, struct ofl_flow_key* key, uint64_t time)
{
  struct flow* ret_flow = NULL;
  struct mini_flow_table *nxt_mft, *tmp;
  long int cur_priority = -1;
  /* Check all the mini flow tables */
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    struct flow tmp_flow;
    struct flow* flow_found;
    /* Cannot modify the flow key, so copy it to a temporary struct. */
    memcpy(&tmp_flow.key, key, sizeof(struct ofl_flow_key));
    /* Apply mini flow table mask to the temporary flow key fields. */
    apply_all_mask(&tmp_flow, &nxt_mft->mask);
    /* Search for a match in the mini flow table. */
    HASH_FIND(hh, nxt_mft->flows, &tmp_flow.key, sizeof(struct ofl_flow_key),
              flow_found);
    if (flow_found) {
      bool expired = flow_table_del_expired(ft, nxt_mft, flow_found, time);
      if (!expired) {
        if (flow_found->priority > cur_priority) {
          /* Take the flow found if priority is
           *  higher than the last one found. */
          cur_priority = flow_found->priority;
          ret_flow = flow_found;
        }
      }
    }
  }
  if (ret_flow) {
    ret_flow->last_used = time;
  }
  return ret_flow;
}

/* Insert flow:
*  added = False
*  for each flow hash table
*      if table mask == flow_mask
*          Insert in the hash table
*          added = True
*          break
*   if not added
*      Create a new hash table
*      Insert the flow in the hash table
*/
void
add_flow(struct flow_table* ft, struct flow* f, uint64_t time)
{
  bool added = false;
  struct mini_flow_table* nxt_mft;
  /* Check if a mini flow table for the flow exists.*/
  f->remove_at = f->hard_timeout + time;
  f->last_used = time + f->idle_timeout;
  DL_FOREACH(ft->flows, nxt_mft)
  {
    /* Masks are equal if a mini flow table exists. */
    if (flow_key_cmp(&f->mask, &nxt_mft->mask)) {
      mini_flow_table_add_flow(nxt_mft, f);
      added = true;
    }
  }
  if (!added) {
    mini_flow_table_new(ft, f);
  }
}

/* Strict match only matches when table mask = flow_mask (the flow natural
 * mask)*/

/* Modify flow strict:
*   for each flow hash table
*       if table mask == flow_mask
*          if flow in the hash table and equal priority
*               modify flow
*/
static void
mod_flow_strict(struct flow_table* ft, struct flow* f, uint64_t time)
{
  struct mini_flow_table *nxt_mft, *tmp;
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    if (flow_key_cmp(&f->mask, &nxt_mft->mask)) {
      struct flow* flow_found;
      HASH_FIND(hh, nxt_mft->flows, &f->key, sizeof(struct ofl_flow_key),
                flow_found);
      /* If the flow exists and not expired, replaces its instructions. */
      if (flow_found) {
        bool expired = flow_table_del_expired(ft, nxt_mft, flow_found, time);
        if (!expired) {
          if (flow_found->priority == f->priority) {
            flow_add_instructions(flow_found, f->insts);
          }
        }
      }
      /* Break the loop, the match cannot exist in another flow. */
      break;
    }
  }
}

static void
mod_flow_non_strict(struct flow_table* ft, struct flow* f, uint64_t time)
{
  struct mini_flow_table *nxt_mft, *tmp;
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    struct flow tmp_flow;
    memcpy(&tmp_flow.mask, &nxt_mft->mask, sizeof(struct ofl_flow_key));
    /* Apply modifying flow mask to temporary flow. */
    apply_all_mask(&tmp_flow, &f->mask);
    /* Check if the flow can be found in a mini table. */
    if (flow_key_cmp(&tmp_flow.mask, &f->mask)) {
      struct flow* cur_flow;
      for (cur_flow = nxt_mft->flows; cur_flow != NULL;
           cur_flow = cur_flow->hh.next) {
        /* Copy table flow key. */
        memcpy(&tmp_flow.key, &cur_flow->key, sizeof(struct ofl_flow_key));
        /* Apply modifying flow mask to table flow. */
        apply_all_mask(&tmp_flow, &f->mask);
        if (flow_key_cmp(&tmp_flow.key, &f->key)) {
          bool expired = flow_table_del_expired(ft, nxt_mft, cur_flow, time);
          if (!expired) {
            /* Replace instructions. */
            flow_add_instructions(cur_flow, f->insts);
          }
        }
      }
    }
  }
}

void
modify_flow(struct flow_table* ft, struct flow* f, bool strict, uint64_t time)
{
  if (strict) {
    mod_flow_strict(ft, f, time);
  } else {
    mod_flow_non_strict(ft, f, time);
  }
}

/* Delete flow strict:
*   found = 0
*   for each flow hash table
*       if table mask == flow_mask
*          if flow in the hash table and equal priority
*               delete flow
                found = 1
*   if not found
*      return error
*/
static void
del_flow_strict(struct flow_table* ft, struct flow* f)
{
  struct mini_flow_table *nxt_mft, *tmp;
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    if (flow_key_cmp(&f->mask, &nxt_mft->mask)) {
      struct flow* flow_found;
      HASH_FIND(hh, nxt_mft->flows, &f->key, sizeof(struct ofl_flow_key),
                flow_found);
      /* If the flow exists, delete it. */
      if (flow_found && flow_found->priority == f->priority) {
        flow_table_del_flow(ft, nxt_mft, flow_found);
      }
      /* Break the loop, the match cannot exist in another flow. */
      break;
    }
  }
}

static void
del_flow_non_strict(struct flow_table* ft, struct flow* f)
{
  struct mini_flow_table *nxt_mft, *tmp;
  DL_FOREACH_SAFE(ft->flows, nxt_mft, tmp)
  {
    struct flow tmp_flow;
    memcpy(&tmp_flow.mask, &nxt_mft->mask, sizeof(struct ofl_flow_key));
    /* Apply modifying flow mask to temporary flow. */
    apply_all_mask(&tmp_flow, &f->mask);
    /* Check if the flow can be found in a mini table. */
    if (flow_key_cmp(&tmp_flow.mask, &f->mask)) {
      struct flow *cur_flow, *tmp;
      HASH_ITER(hh, nxt_mft->flows, cur_flow, tmp)
      {
        /* Copy table flow key */
        memcpy(&tmp_flow.key, &cur_flow->key, sizeof(struct ofl_flow_key));
        /* Apply modifying flow mask to table flow. */
        apply_all_mask(&tmp_flow, &f->mask);

        if (flow_key_cmp(&tmp_flow.key, &f->key)) {
          /* Delete flow */
          flow_table_del_flow(ft, nxt_mft, cur_flow);
        }
      }
    }
  }
}

void
delete_flow(struct flow_table* ft, struct flow* f, bool strict)
{
  if (strict) {
    del_flow_strict(ft, f);
  } else {
    del_flow_non_strict(ft, f);
  }
}
