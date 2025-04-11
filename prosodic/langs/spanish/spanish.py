from ..langs import LanguageModel, cache

stress2stroke = {0:'', 1:"'"}

orth2phon = {}

# Vowels
orth2phon['a'] = ['a']
orth2phon['e'] = ['e']
orth2phon['i'] = ['i']
orth2phon['o'] = ['o']
orth2phon['u'] = ['u']
orth2phon['ü'] = ['w']  # used in güe/güi

# Diphthongs
orth2phon['ai'] = ['aj']
orth2phon['ei'] = ['ej']
orth2phon['oi'] = ['oj']
orth2phon['au'] = ['aw']
orth2phon['eu'] = ['ew']
orth2phon['ou'] = ['ow']
orth2phon['ia'] = ['ja']
orth2phon['ie'] = ['je']
orth2phon['io'] = ['jo']
orth2phon['ua'] = ['wa']
orth2phon['ue'] = ['we']
orth2phon['uo'] = ['wo']

# Consonants
orth2phon['b'] = ['b']
orth2phon['c'] = ['k']  # before a, o, u
orth2phon['ce'] = ['θ']  # in Spain; use ['s'] for Latin America
orth2phon['ci'] = ['θ']
orth2phon['ch'] = ['tʃ']
orth2phon['d'] = ['d']
orth2phon['f'] = ['f']
orth2phon['g'] = ['g']  # before a, o, u
orth2phon['ge'] = ['x']
orth2phon['gi'] = ['x']
orth2phon['gu'] = ['g']  # before e/i when ü is not used
orth2phon['gü'] = ['gw']
orth2phon['h'] = []  # silent
orth2phon['j'] = ['x']
orth2phon['k'] = ['k']
orth2phon['l'] = ['l']
orth2phon['ll'] = ['ʝ']  # or ['ʎ'] in some regions
orth2phon['m'] = ['m']
orth2phon['n'] = ['n']
orth2phon['ñ'] = ['ɲ']
orth2phon['p'] = ['p']
orth2phon['q'] = ['k']
orth2phon['qu'] = ['k']
orth2phon['r'] = ['ɾ']  # flap
orth2phon['rr'] = ['r']  # trill
orth2phon['s'] = ['s']
orth2phon['t'] = ['t']
orth2phon['v'] = ['b']  # same as b in most dialects
orth2phon['w'] = ['w']
orth2phon['x'] = ['ks']
orth2phon['y'] = ['ʝ']
orth2phon['z'] = ['θ']  # ['s'] in Latin America

ipa2x=dict([("".join(v), k) for (k, v) in orth2phon.items()])


class SpanishLanguage(LanguageModel):
    lang = 'es'
    name = 'spanish'
    lang_espeak = 'es-es'

@cache
def Spanish(): return SpanishLanguage()
