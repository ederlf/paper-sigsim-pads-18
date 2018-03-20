#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include "lib/heap.h"

void *dataplane(void* heap);
void *listener(void* heap);
pthread_mutex_t mutex1 = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t condA  = PTHREAD_COND_INITIALIZER;
int  run = 1;
int stop_dp = 1;
int counter = 2;
int current_time = 0;

static
void heap_display(struct heap *h) {
    size_t i;
    for(i=1; i <= h->size; ++i) {
        printf("|%ld|", h->array[i]->priority);
    }
    printf("\n");
}

main()
{
   int rc1, rc2, i;
   pthread_t thread1, thread2;
   struct heap *h = malloc(sizeof(struct heap));
   for (i = 0; i < counter; ++i) {
      struct heap_node *node = malloc(sizeof(struct heap_node));
       heap_insert(h, node, i);
   }
   /* Create independent threads each of which will execute functionC */

   if( (rc1=pthread_create( &thread1, NULL, &dataplane, (void*)h)) )
   {
      printf("Thread creation failed: %d\n", rc1);
   }

   if( (rc2=pthread_create( &thread2, NULL, &listener, (void*)h)) )
   {
      printf("Thread creation failed: %d\n", rc2);
   }

   /* Wait till threads are complete before main continues. Unless we  */
   /* wait we run the risk of executing an exit which will terminate   */
   /* the process and all threads before the threads have completed.   */

   pthread_join( thread1, NULL);
   pthread_join( thread2, NULL); 

   free(h);

   exit(EXIT_SUCCESS);
}

void *dataplane(void* heap)
{
   struct heap *h = (struct heap*) heap;
   int i;
   while(h->size){
      pthread_mutex_lock(&mutex1);
      while (stop_dp)
            pthread_cond_wait(&condA, &mutex1);
      pthread_mutex_unlock(&mutex1);
      pthread_mutex_lock( &mutex1 );
      struct heap_node *node = heap_delete(h);
      current_time = node->priority;
      /* code */
      pthread_mutex_unlock( &mutex1 );
      printf("Executing %ld\n", node->priority);
      free(node);
      
   }
   run = 0;
   // counter++;
   // printf("Counter value: %d\n",counter);
}

void *listener(void* heap)
{
   struct heap *h = (struct heap*) heap;
   while(run){
      pthread_mutex_lock(&mutex1);
      stop_dp = 1;
      pthread_mutex_unlock( &mutex1 );
      struct heap_node *node = malloc(sizeof(struct heap_node));
      pthread_mutex_lock( &mutex1 );
      printf("Creating new event %d\n", current_time);
      heap_insert(h, node, current_time);
      stop_dp = 0;
      pthread_cond_signal(&condA);
      pthread_mutex_unlock( &mutex1 );
   }
}
