#!/usr/bin/env python3
"""trie - Trie (prefix tree) for autocomplete, spell-check, and prefix search."""

import sys, json, os

class TrieNode:
    __slots__ = ('children', 'is_end', 'count', 'data')
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.count = 0
        self.data = None

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.size = 0

    def insert(self, word, data=None):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            node.count += 1
        if not node.is_end:
            self.size += 1
        node.is_end = True
        if data is not None:
            node.data = data

    def search(self, word):
        node = self._find(word)
        return node is not None and node.is_end

    def _find(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def starts_with(self, prefix):
        return self._find(prefix) is not None

    def autocomplete(self, prefix, limit=10):
        node = self._find(prefix)
        if not node:
            return []
        results = []
        self._collect(node, prefix, results, limit)
        return results

    def _collect(self, node, prefix, results, limit):
        if len(results) >= limit:
            return
        if node.is_end:
            results.append(prefix)
        for ch in sorted(node.children):
            self._collect(node.children[ch], prefix + ch, results, limit)
            if len(results) >= limit:
                return

    def prefix_count(self, prefix):
        node = self._find(prefix)
        return node.count if node else 0

    def delete(self, word):
        def _del(node, word, depth):
            if depth == len(word):
                if not node.is_end:
                    return False
                node.is_end = False
                self.size -= 1
                return len(node.children) == 0
            ch = word[depth]
            if ch not in node.children:
                return False
            should_del = _del(node.children[ch], word, depth + 1)
            if should_del:
                del node.children[ch]
                return not node.is_end and len(node.children) == 0
            node.children[ch].count -= 1
            return False
        _del(self.root, word, 0)

    def all_words(self):
        results = []
        self._collect(self.root, '', results, float('inf'))
        return results

    def _to_dict(self, node):
        d = {}
        if node.is_end:
            d['$'] = True
        if node.data is not None:
            d['_data'] = node.data
        for ch, child in sorted(node.children.items()):
            d[ch] = self._to_dict(child)
        return d

    def _from_dict(self, d, node):
        node.is_end = d.get('$', False)
        node.data = d.get('_data')
        if node.is_end:
            self.size += 1
        for ch, child_d in d.items():
            if ch in ('$', '_data'):
                continue
            child = TrieNode()
            node.children[ch] = child
            self._from_dict(child_d, child)
            child.count = sum(c.count for c in child.children.values()) + (1 if child.is_end else 0)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self._to_dict(self.root), f)

    def load(self, path):
        with open(path) as f:
            d = json.load(f)
        self.root = TrieNode()
        self.size = 0
        self._from_dict(d, self.root)

    def suggest(self, word, max_dist=2):
        """Fuzzy search using edit distance."""
        results = []
        row = list(range(len(word) + 1))
        for ch, child in self.root.children.items():
            self._suggest_rec(child, ch, word, row, results, max_dist)
        results.sort(key=lambda x: x[1])
        return results

    def _suggest_rec(self, node, built, word, prev_row, results, max_dist):
        cols = len(word) + 1
        cur_row = [prev_row[0] + 1]
        for col in range(1, cols):
            cost = 0 if word[col-1] == built[-1] else 1
            cur_row.append(min(cur_row[col-1]+1, prev_row[col]+1, prev_row[col-1]+cost))
        if cur_row[-1] <= max_dist and node.is_end:
            results.append((built, cur_row[-1]))
        if min(cur_row) <= max_dist:
            for ch, child in node.children.items():
                self._suggest_rec(child, built + ch, word, cur_row, results, max_dist)

def get_trie(args):
    path = None; rest = []
    i = 0
    while i < len(args):
        if args[i] in ('-f', '--file'): path = args[i+1]; i += 2
        else: rest.append(args[i]); i += 1
    t = Trie()
    if path and os.path.exists(path):
        t.load(path)
    return t, path, rest

def cmd_add(args):
    t, path, words = get_trie(args)
    if not words:
        words = [l.strip() for l in sys.stdin if l.strip()]
    for w in words:
        t.insert(w)
    print(f"Added {len(words)} ({t.size} total)")
    if path: t.save(path)

def cmd_search(args):
    t, _, rest = get_trie(args)
    for w in rest:
        print(f"{'✓' if t.search(w) else '✗'} {w}")

def cmd_complete(args):
    t, _, rest = get_trie(args)
    limit = 10
    prefix = rest[0] if rest else ''
    for w in t.autocomplete(prefix, limit):
        print(w)

def cmd_fuzzy(args):
    t, _, rest = get_trie(args)
    dist = 2
    word = rest[0]
    for w, d in t.suggest(word, dist):
        print(f"  {w} (distance: {d})")

def cmd_list(args):
    t, _, _ = get_trie(args)
    for w in t.all_words():
        print(w)

def cmd_stats(args):
    t, _, _ = get_trie(args)
    print(f"Words: {t.size}")
    words = t.all_words()
    if words:
        avg = sum(len(w) for w in words) / len(words)
        print(f"Avg length: {avg:.1f}")
        print(f"Shortest: {min(words, key=len)}")
        print(f"Longest: {max(words, key=len)}")

def cmd_delete(args):
    t, path, rest = get_trie(args)
    for w in rest:
        t.delete(w)
        print(f"DEL {w}")
    if path: t.save(path)

CMDS = {
    'add': (cmd_add, '-f FILE WORD [...] — insert words'),
    'search': (cmd_search, '-f FILE WORD [...] — exact search'),
    'complete': (cmd_complete, '-f FILE PREFIX — autocomplete'),
    'fuzzy': (cmd_fuzzy, '-f FILE WORD — fuzzy search (edit distance)'),
    'list': (cmd_list, '-f FILE — list all words'),
    'stats': (cmd_stats, '-f FILE — trie statistics'),
    'delete': (cmd_delete, '-f FILE WORD [...] — remove words'),
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("Usage: trie <command> [args...]")
        for n, (_, d) in sorted(CMDS.items()):
            print(f"  {n:10s} {d}")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd not in CMDS: print(f"Unknown: {cmd}", file=sys.stderr); sys.exit(1)
    CMDS[cmd][0](sys.argv[2:])

if __name__ == '__main__':
    main()
