import sys

hf = "/home/vagrant/sigsim_pads/graphs/data/horse_rates-%s.txt" % (sys.argv[1])
mf = "/home/vagrant/sigsim_pads/graphs/data/mn_rates-%s.txt" % (sys.argv[1])

path = "/home/vagrant/sigsim_pads/graphs/data/results-rate/"

# Return a list with the average bw
def calculate_avg_bw(fname):
    vlist = []
    try:
        with file(fname, "r") as f:
            lines = f.readlines()
            values = []
            idx = 0    
            for line in lines[1:]:
                if line == "\n":
                    cp_values = values
                    vlist.append(cp_values)
                    values = []
                else:
                    line = line.strip("\n")
                    values.append(float(line))
        zipped_list = zip(*vlist)

        return [sum(item)/len(vlist) for item in zipped_list]
    except Exception as e:
        print ("File %s not found" % fname)
        sys.exit(0)

def write_data(horse_list, mn_list):
    with file("%sk-%s.dat" % (path, sys.argv[1]), "w") as f:
        f.write("%s %s %s\n" % (0, 0, 0))
        t = 1
        for pair in zip(horse_list, mn_list):
            f.write("%s %s %s\n" % (t, pair[0], pair[1])) 
            t += 1

hl = calculate_avg_bw(hf)
ml = calculate_avg_bw(mf)
# print zip(hl, ml)
write_data(hl, ml)