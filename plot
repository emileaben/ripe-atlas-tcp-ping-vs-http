set term pdf size 5,5
unset key
set grid

#set xrange [-5:5]
#set output "test.pdf"
#set xlabel "TCP faster <---- TCP-ICMP/FASTEST (%) ----> ICMP faster"
#plot "plot-vals" u 1:rand(0)

# diff = 100.0*(tcp10-icmp10)/min(tcp10,icmp10)
## tcp=10ms  icmp=20ms  ->   (10-20)/10 = -100%  <- minus = tcp is faster
## tcp=20ms  icmp=10ms  ->   (20-10)/10 = +100%  <- plus  = icmp is faster

f(x) = x

set output "rtt.pdf"
set title "Comparison of RTTs of 9k probe-anchor pairs"
set xrange [0:200]
set yrange [0:200]
set xlabel "TCP RTT (10th percentile, ms)"
set ylabel "ICMP RTT (10th percentile, ms)"
plot "analysed-msm.txt" u 4:5 w dots lc rgb "#aa000077", f(x)


set xrange [0:50]
set yrange [0:50]
set title "Comparison of RTTs of 9k probe-anchor pairs (zoom)"
set output "rtt-zoom.pdf"
replot

# color by v4-v6
set palette defined (3.9 "#770000", 4.1 "#770000", 5.9 "#007700", 6.1 "#007700")
set title "Comparison of RTTs of 9k probe-anchor pairs\n(zoom,colored by IPv4/IPv6)"
set output "rtt-zoom-v4v6.pdf"
plot "analysed-msm.txt" u 4:5:3 with dots palette


set output "rtt-zoom-v6.pdf"
set title "Comparison of RTTs of 9k probe-anchor pairs\n(zoom,IPv6 only)"
plot "< cat analysed-msm.txt | perl -lane'print if $F[2]==6'" u 4:5 with dots lc rgb "#aa000077", f(x)

# scatter color by probe_id
set palette rgb 30,31,32
set output "rtt-zoom-byprobe.pdf"
set title "Comparison of RTTs of 9k probe-anchor pairs\n(zoom,color by probe ID)"
plot "analysed-msm.txt" u 4:5:1 with dots palette, f(x)

set output "rtt

set output "loss.pdf"
set title "Comparison of loss of 9k probe-anchor pairs"
set xrange [0:1.01]
set yrange [0:1.01]
set xlabel "success rate on TCP"
set ylabel "success rate on ICMP"
plot "loss.txt" u 4:5 w dots lc rgb "#aa000099", f(x)

set output "loss-zoom.pdf"
set title "Comparison of loss of 9k probe-anchor pairs\n(zoom)"
set xrange [0.9:1.001]
set yrange [0.9:1.001]
replot

set output "loss-zoom-v4v6.pdf"
set title "Comparison of loss of 9k probe-anchor pairs\n(zoom,colored by IPv4/IPv6)"
set palette defined (3.9 "#770000", 4.1 "#770000", 5.9 "#007700", 6.1 "#007700")
plot "loss.txt" u 4:5:3 with dots palette

set palette rgb 30,31,32
set output "loss-zoom-byprobe.pdf"
set title "Comparison of loss of 9k probe-anchor pairs\n(zoom,colored by probe ID)"
plot "loss.txt" u 4:5:1 with dots palette, f(x)
