set border linecolor rgbcolor "{{ color }}"
set key textcolor rgbcolor "{{ color }}"

set xlabel "{{ xlabel }}" textcolor rgbcolor "{{ color }}"
set ylabel "{{ ylabel }}" textcolor rgbcolor "{{ color }}"
#set title "{{ title }}" textcolor rgbcolor "{{ color }}"

set key {{ legend }}
set grid

set terminal svg dynamic enhanced fname "helvetica" size {{ width }},{{ height }}
set output "{{ outputfile }}.svg"

{{ appendText }}

{{ plots }}

# Extra
#set logscale y
#set xtics font ",8"
#set timefmt "%H:%M"
#set timefmt "%H:%M:%S"
#set timefmt "%d.%m.%Y"
#set xdata time
#set format x "%d.%m.%Y"
#set ydata time
#set format y "%H:%M:%S"
#set xrange ["00:00":"24:00"]
#set key autotitle columnhead

#set xtics rotate by -90

#set style data lines
#set style histogram clustered gap 4
#set boxwidth 0.8 relative

#set samples 1000
