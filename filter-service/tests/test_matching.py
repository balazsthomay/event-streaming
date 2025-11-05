# Unit tests for filter matching

import sys
sys.path.append('..')  # So we can import from parent directory

from filter_service import matches_criteria

def test_matches_criteria_for_valid_purchase():
    event = {
        'eventType': 'purchase',
        'userTier': 'premium',
        'amount': 100
    }
    criteria = {
        'event_types': ['purchase'],
        'user_tiers': ['premium'],
        'min_amount': 50
    }
    result = matches_criteria(event, criteria)
    assert result == True

def test_click_event_should_not_match_purchase_filter():
    event = {
        'eventType': 'click',
        'userTier': 'premium',
        'amount': None
    }
    criteria = {
        'event_types': ['purchase'],
        'user_tiers': ['premium'],
        'min_amount': None
    }
    result = matches_criteria(event, criteria)
    assert result == False
    
# event is a click, but criteria wants purchases
def test_free_user_should_not_match_premium_filter():
    event = {
        'eventType': 'purchase',
        'userTier': 'free',
        'amount': None
    }
    criteria = {
        'event_types': ['purchase'],
        'user_tiers': ['premium'],
        'min_amount': None
    }
    
    result = matches_criteria(event, criteria)
    
    assert result == False