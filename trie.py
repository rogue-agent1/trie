#!/usr/bin/env python3
"""trie - Trie data structure with search. Zero deps."""
import sys,json
class Trie:
    def __init__(s):s.root={}
    def insert(s,word):
        n=s.root
        for c in word:n=n.setdefault(c,{})
        n['$']=True
    def search(s,word):
        n=s.root
        for c in word:
            if c not in n:return False
            n=n[c]
        return '$' in n
    def prefix(s,pre):
        n=s.root;results=[]
        for c in pre:
            if c not in n:return[]
            n=n[c]
        def collect(node,p):
            if '$' in node:results.append(p)
            for c,child in node.items():
                if c!='$':collect(child,p+c)
        collect(n,pre);return results
def main():
    t=Trie()
    if len(sys.argv)>1 and sys.argv[1]=='--file':
        for w in open(sys.argv[2]).read().split():t.insert(w.lower())
        q=sys.argv[3] if len(sys.argv)>3 else input('Prefix: ')
        results=t.prefix(q.lower())
        print(f'{len(results)} matches: {", ".join(results[:20])}')
    else:
        words=sys.argv[1:] or ['hello','help','heap','world','work']
        for w in words:t.insert(w)
        print('Words:',words)
        for w in['hel','wor','xyz']:print(f'Prefix "{w}": {t.prefix(w)}')
if __name__=='__main__':main()
