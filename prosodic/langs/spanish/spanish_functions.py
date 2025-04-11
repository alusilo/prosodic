from ...imports import *

def is_vowel(char):
    """Check if a character is a Spanish vowel"""
    return char.lower() in {'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú'}

def is_consonant(char):
    """Check if a character is a Spanish consonant"""
    return char.lower() in {'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 
                          'n', 'ñ', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z'}

def is_strong_vowel(char):
    """Check if a vowel is strong (a, e, o)"""
    return char.lower() in {'a', 'e', 'o', 'á', 'é', 'ó'}

def is_weak_vowel(char):
    """Check if a vowel is weak (i, u)"""
    return char.lower() in {'i', 'u', 'í', 'ú'}

def is_diphthong(v1, v2):
    """Check if two vowels form a diphthong"""
    # Diphthong rules:
    # 1. Weak + Strong
    # 2. Strong + Weak
    # 3. Weak + Weak
    return (is_weak_vowel(v1) and is_strong_vowel(v2)) or \
           (is_strong_vowel(v1) and is_weak_vowel(v2)) or \
           (is_weak_vowel(v1) and is_weak_vowel(v2))

def is_triphthong(v1, v2, v3):
    """Check if three vowels form a triphthong"""
    # Triphthong rules:
    # Weak + Strong + Weak
    return is_weak_vowel(v1) and is_strong_vowel(v2) and is_weak_vowel(v3)

def get_syllable_weight(syllable):
    """Calculate syllable weight for Spanish"""
    # Spanish syllable weight rules:
    # 1. Light syllable: ends in short vowel
    # 2. Heavy syllable: ends in long vowel, diphthong, or consonant
    
    vowels = {'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú'}
    long_vowels = {'á', 'é', 'í', 'ó', 'ú'}
    
    # Check for diphthong/triphthong
    vowel_count = sum(1 for c in syllable if c in vowels)
    if vowel_count >= 2:
        return 2  # Heavy
    
    # Check for long vowel
    if any(c in syllable for c in long_vowels):
        return 2  # Heavy
    
    # Check for coda consonant
    if syllable[-1].lower() not in vowels:
        return 2  # Heavy
    
    return 1  # Light

def get_word_stress_pattern(word):
    """Get the stress pattern of a Spanish word"""
    # Spanish stress patterns:
    # 1. Aguda: stress on last syllable
    # 2. Llana: stress on penultimate syllable
    # 3. Esdrújula: stress on antepenultimate syllable
    # 4. Sobresdrújula: stress before antepenultimate syllable
    
    # Import syllabify here to avoid circular import
    from .spanish_annotator import syllabify
    
    syllables = syllabify(word)
    num_syllables = len(syllables)
    
    # Check for written accent
    for i, syll in enumerate(syllables):
        if any(c in syll for c in ['á', 'é', 'í', 'ó', 'ú']):
            if i == num_syllables - 1:
                return "aguda"
            elif i == num_syllables - 2:
                return "llana"
            elif i == num_syllables - 3:
                return "esdrújula"
            else:
                return "sobresdrújula"
    
    # No written accent, apply default rules
    if word[-1].lower() in {'a', 'e', 'i', 'o', 'u', 'n', 's'}:
        return "llana"
    else:
        return "aguda"

def get_sonority_hierarchy(char):
    """Get the sonority value for a Spanish phoneme"""
    # Spanish sonority hierarchy (from least to most sonorous):
    # 1. Stops: p, t, k, b, d, g
    # 2. Fricatives: f, s, x, j
    # 3. Nasals: m, n, ñ
    # 4. Liquids: l, r, rr
    # 5. Glides: y, w
    # 6. Vowels
    
    stops = {'p', 't', 'k', 'b', 'd', 'g'}
    fricatives = {'f', 's', 'x', 'j'}
    nasals = {'m', 'n', 'ñ'}
    liquids = {'l', 'r', 'rr'}
    glides = {'y', 'w'}
    vowels = {'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú'}
    
    if char in stops:
        return 1
    elif char in fricatives:
        return 2
    elif char in nasals:
        return 3
    elif char in liquids:
        return 4
    elif char in glides:
        return 5
    elif char in vowels:
        return 6
    else:
        return 0

def is_hiatus(v1, v2):
    """Check if two vowels form a hiatus"""
    # Hiatus rules:
    # 1. Two strong vowels
    # 2. Same vowel repeated
    # 3. Stressed weak vowel + any vowel
    return (is_strong_vowel(v1) and is_strong_vowel(v2)) or \
           (v1.lower() == v2.lower()) or \
           (v1 in {'í', 'ú'} and is_vowel(v2))

def is_syllabic_consonant(char):
    """Check if a consonant can be syllabic in Spanish"""
    # In Spanish, only 'l' and 'r' can be syllabic in certain contexts
    return char.lower() in {'l', 'r'}

def is_voiced_consonant(char):
    """Check if a consonant is voiced in Spanish"""
    voiced = {'b', 'd', 'g', 'v', 'w', 'z', 'j', 'l', 'm', 'n', 'ñ', 'r', 'y'}
    return char.lower() in voiced

def is_voiceless_consonant(char):
    """Check if a consonant is voiceless in Spanish"""
    voiceless = {'p', 't', 'k', 'f', 's', 'x', 'ch', 'h'}
    return char.lower() in voiceless 