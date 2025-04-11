from ...imports import *

# German phonetic constants
VOWELS = 'aeiouäöüy'
CONSONANTS = 'bcdfghjklmnpqrstvwxzß'
DIPHTHONGS = ['ai', 'ei', 'au', 'äu', 'eu', 'ie']
SCHWAS = ['e']  # In German, final 'e' is often schwa sound

# Legal German onset clusters (incomplete list, extend as needed)
LEGAL_ONSETS = {
    'bl', 'br', 'ch', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 
    'kl', 'kn', 'kr', 'pf', 'ph', 'pl', 'pr', 'qu', 'sc', 'sch', 
    'schl', 'schm', 'schn', 'schr', 'schw', 'sk', 'sl', 'sm', 'sn', 
    'sp', 'spl', 'spr', 'st', 'str', 'sw', 'th', 'tr', 'tw', 'vl', 
    'vr', 'wr', 'zw'
}

# Helper functions
def is_vowel(char):
    """
    Check if a character is a vowel.
    
    Args:
        char (str): The character to check
        
    Returns:
        bool: True if the character is a vowel
    """
    return char.lower() in VOWELS


def is_diphthong(chars):
    """
    Check if a character sequence is a diphthong.
    
    Args:
        chars (str): The characters to check
        
    Returns:
        bool: True if the characters form a diphthong
    """
    return chars.lower() in DIPHTHONGS


def is_schwa(char, position=None):
    """
    Check if a character represents a schwa sound.
    
    Args:
        char (str): The character to check
        position (str, optional): Position in the word ('final', 'medial', etc.)
        
    Returns:
        bool: True if the character represents a schwa sound
    """
    # In German, 'e' at the end of words is usually a schwa
    if char.lower() in SCHWAS:
        if position == 'final':
            return True
        # In unstressed syllables, 'e' can be a schwa
        return True
    return False


def is_consonant(char):
    """
    Check if a character is a consonant.
    
    Args:
        char (str): The character to check
        
    Returns:
        bool: True if the character is a consonant
    """
    return char.lower() in CONSONANTS


def is_heavy_syllable(onset, nucleus, coda):
    """
    Check if a syllable is heavy (for stress assignment).
    
    Args:
        onset (str): The onset of the syllable
        nucleus (str): The nucleus of the syllable
        coda (str): The coda of the syllable
        
    Returns:
        bool: True if the syllable is heavy
    """
    # A syllable is heavy if it has a long vowel/diphthong or a complex coda
    if is_diphthong(nucleus):
        return True
    if len(coda) > 0:
        return True
    return False


def is_long_vowel(vowel, context=""):
    """Check if a vowel is long in German based on context"""
    # German long vowel rules:
    # 1. Double vowel (aa, ee, oo)
    # 2. Vowel + h (ah, eh, oh)
    # 3. ie is always long
    # 4. Open syllable (vowel at end of syllable)
    # 5. Stressed syllable with single vowel followed by single consonant
    
    if not vowel:
        return False
        
    vowel = vowel.lower()
    
    # Double vowel
    if len(vowel) == 2 and vowel[0] == vowel[1]:
        return True
        
    # Vowel + h
    if len(vowel) == 2 and vowel[1] == 'h':
        return True
        
    # ie is always long
    if vowel == 'ie':
        return True
        
    # Context-dependent cases
    if context == "open":  # Open syllable
        return True
        
    if context == "stressed_followed_by_single_consonant":
        return True
        
    return False


def get_syllable_weight(syllable):
    """Calculate syllable weight for German"""
    # German syllable weight rules:
    # 1. Light syllable: ends in short vowel (open syllable)
    # 2. Heavy syllable: ends in long vowel, diphthong, or consonant
    
    if not syllable:
        return 0
    
    # Split syllable into onset, nucleus, coda
    onset, nucleus, coda = split_syllable(syllable)
    
    # Check for diphthong
    if is_diphthong(nucleus):
        return 2  # Heavy
    
    # Check for long vowel
    if is_long_vowel(nucleus, "open" if not coda else ""):
        return 2  # Heavy
    
    # Check for closed syllable (has coda)
    if coda:
        return 2  # Heavy
    
    # Open syllable with short vowel
    return 1  # Light


def apply_consonant_cluster_rules(consonant_group):
    """
    Determine how to split consonant clusters between syllables.
    
    Args:
        consonant_group (str): The consonant group to analyze
        
    Returns:
        int: The position where to split the consonants
    """
    if not consonant_group:
        return 0
        
    # Legal onset clusters stay together
    for i in range(min(len(consonant_group), 4), 0, -1):
        if consonant_group[-i:] in LEGAL_ONSETS:
            return len(consonant_group) - i
    
    # Single consonant goes to the next syllable
    if len(consonant_group) == 1:
        return 0
        
    # Default: Split before the last consonant
    return len(consonant_group) - 1


def split_syllable(syllable):
    """
    Split a syllable into onset, nucleus, and coda.
    
    Args:
        syllable (str): The syllable to split
        
    Returns:
        tuple: (onset, nucleus, coda)
    """
    if not syllable:
        return ('', '', '')
    
    syllable = syllable.lower()
    
    # Find nucleus (vowel or diphthong)
    nucleus_start = None
    nucleus_end = None
    
    # First check for diphthongs
    for i in range(len(syllable) - 1):
        if is_diphthong(syllable[i:i+2]):
            nucleus_start = i
            nucleus_end = i + 2
            break
    
    # If no diphthong found, look for single vowels
    if nucleus_start is None:
        for i, char in enumerate(syllable):
            if is_vowel(char):
                nucleus_start = i
                nucleus_end = i + 1
                break
    
    # If no vowel found, treat as all consonant
    if nucleus_start is None:
        return (syllable, '', '')
    
    # Get onset, nucleus, and coda
    onset = syllable[:nucleus_start]
    nucleus = syllable[nucleus_start:nucleus_end]
    coda = syllable[nucleus_end:]
    
    return (onset, nucleus, coda)


def classify_consonant(char):
    """Classify a consonant by manner and place of articulation"""
    # German consonant classification
    
    char = char.lower()
    
    # Stops (plosives)
    if char in 'bpdtgk':
        voicing = 'voiced' if char in 'bdg' else 'voiceless'
        if char in 'bp':
            place = 'bilabial'
        elif char in 'dt':
            place = 'alveolar'
        else:  # g, k
            place = 'velar'
        return {'manner': 'stop', 'place': place, 'voicing': voicing}
    
    # Fricatives
    elif char in 'fvszßhjx':
        voicing = 'voiced' if char in 'vzj' else 'voiceless'
        if char in 'fv':
            place = 'labiodental'
        elif char in 'szß':
            place = 'alveolar'
        elif char == 'j':
            place = 'palatal'
        elif char == 'x':
            place = 'velar'
        elif char == 'h':
            place = 'glottal'
        else:
            place = 'unknown'
        return {'manner': 'fricative', 'place': place, 'voicing': voicing}
    
    # Nasals
    elif char in 'mn':
        place = 'bilabial' if char == 'm' else 'alveolar'
        return {'manner': 'nasal', 'place': place, 'voicing': 'voiced'}
    
    # Liquids
    elif char in 'lr':
        type_of = 'lateral' if char == 'l' else 'rhotic'
        return {'manner': type_of, 'place': 'alveolar', 'voicing': 'voiced'}
    
    # Other
    return {'manner': 'other', 'place': 'unknown', 'voicing': 'unknown'}

def get_word_stress_pattern(word):
    """Get the stress pattern of a German word"""
    # German stress patterns:
    # 1. Default: stress on first syllable
    # 2. Prefixes: usually unstressed
    # 3. Compounds: primary stress on first element
    # 4. Suffixes: some affect stress placement
    
    if not word:
        return "none"
    
    # Define common unstressed prefixes
    prefixes = {'ge', 'be', 'ver', 'zer', 'ent', 'er', 'emp', 'miss'}
    
    # Check if word starts with a common unstressed prefix
    for prefix in prefixes:
        if word.lower().startswith(prefix) and len(word) > len(prefix):
            return "prefix"
    
    # Default to first syllable stress
    return "first"

def get_sonority_hierarchy(char):
    """Get the sonority value for a German phoneme"""
    # German sonority hierarchy (from least to most sonorous):
    # 1. Stops: p, t, k, b, d, g
    # 2. Fricatives: f, s, sch, ch, h
    # 3. Nasals: m, n, ng
    # 4. Liquids: l, r
    # 5. Glides: j, w
    # 6. Vowels
    
    stops = {'p', 't', 'k', 'b', 'd', 'g'}
    fricatives = {'f', 's', 'sch', 'ch', 'h'}
    nasals = {'m', 'n', 'ng'}
    liquids = {'l', 'r'}
    glides = {'j', 'w'}
    vowels = {'a', 'e', 'i', 'o', 'u', 'ä', 'ö', 'ü', 'y'}
    
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

def is_voiced_consonant(char):
    """Check if a consonant is voiced in German"""
    voiced = {'b', 'd', 'g', 'v', 'w', 'z', 'j', 'l', 'm', 'n', 'r'}
    return char.lower() in voiced

def is_voiceless_consonant(char):
    """Check if a consonant is voiceless in German"""
    voiceless = {'p', 't', 'k', 'f', 's', 'ß', 'ch', 'sch', 'h'}
    return char.lower() in voiceless

def is_terminal_devoicing_candidate(char):
    """Check if a consonant is subject to terminal devoicing in German"""
    # In German, voiced obstruents (b, d, g, v, z) are devoiced at the end of a word or syllable
    return char.lower() in {'b', 'd', 'g', 'v', 'z'}

def apply_terminal_devoicing(char):
    """Apply terminal devoicing to a German consonant"""
    devoicing_map = {
        'b': 'p',
        'd': 't',
        'g': 'k',
        'v': 'f',
        'z': 's'
    }
    return devoicing_map.get(char.lower(), char) 