"""Replace a method block in moon.py with the contents of a file.
usage: splice.py file.py "    def start_marker" "    def end_marker" """
import sys
s = open('moon.py', encoding='utf-8').read()
new = open(sys.argv[1], encoding='utf-8').read()
i = s.index(sys.argv[2]); j = s.index(sys.argv[3])
assert i < j
s = s[:i] + new.rstrip('\n') + '\n\n' + s[j:]
open('moon.py', 'w', encoding='utf-8').write(s)
print('spliced', sys.argv[1])
