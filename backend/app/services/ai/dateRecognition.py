import re
from dateparser.search import search_dates

KEYWORD_PRIORITY = {
    "meeting": 2,
    "at": 1
}

def get_word_positions(text):
    words, positions = [], []
    for match in re.finditer(r'\S+', text):
        words.append(match.group())
        positions.append(match.start())
    return words, positions

def find_date_word_index(positions, date_start):
    for i, pos in enumerate(positions):
        if pos >= date_start:
            return i
    return len(positions) - 1

def get_context_words(words, date_index, context_window):
    start_idx = max(0, date_index - context_window)
    end_idx = min(len(words), date_index + context_window + 1)
    return words[start_idx:end_idx]

def extract_dates(email_text, context_window=7):
    results = []
    search_results = search_dates(email_text)
    if not search_results:
        return results

    words, positions = get_word_positions(email_text)
    for matched_str, dt in search_results:
        idx = email_text.find(matched_str)
        if idx == -1:
            continue
        date_index = find_date_word_index(positions, idx)
        context_words = get_context_words(words, date_index, context_window)
        context_text = " ".join(context_words)
        
        best_keyword = None
        best_priority = -1
        best_distance = None
        
        start_idx = max(0, date_index - context_window)
        for i in range(start_idx, min(len(words), date_index + context_window + 1)):
            word = words[i]
            word_lower = word.lower()
            for kw, priority in KEYWORD_PRIORITY.items():
                if kw in word_lower:
                    distance = abs(i - date_index)
                    if priority > best_priority or (priority == best_priority and (best_distance is None or distance < best_distance)):
                        best_priority = priority
                        best_keyword = kw
                        best_distance = distance
        if best_keyword is not None:
            results.append({
                'date': dt,
                'matched_text': matched_str,
                'context': context_text,
                'best_keyword': best_keyword,
                'priority': best_priority,
                'distance': best_distance,
                'date_index': date_index
            })
    return results

def choose_best_date(email_text):
    date_matches = extract_dates(email_text)
    if not date_matches:
        return None
    sorted_matches = sorted(date_matches, key=lambda x: (-x['priority'], x['distance']))
    return sorted_matches[0]['date'].strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    email_text = """
    Dear user,
    
    I hope you are well. Our meeting is scheduled for 2025-04-03 at 10:00 AM.
    Please let me know if that works for you.
    
    Best regards,
    John Doe
    Sent on: March 31, 2025
    """
    
    best_match = choose_best_date(email_text)
    print(best_match)

