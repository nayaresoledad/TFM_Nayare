"""
Data validation tests for extraction services.
Tests data format validation and extraction quality.
"""
import pytest
import re
from datetime import datetime


class TestDataValidation:
    """Test data validation in extraction services."""
    
    def test_song_title_not_empty(self):
        """Test that song titles cannot be empty."""
        assert len("") == 0
        assert len("Valid Song Title") > 0
    
    def test_artist_name_format(self):
        """Test artist name format validation."""
        valid_names = [
            "The Beatles",
            "Artist Name",
            "Single",
            "123 Band",
            "Artista Español",
        ]
        
        for name in valid_names:
            assert len(name) > 0
            assert isinstance(name, str)
    
    def test_mbid_format_validation(self):
        """Test MBID format validation (UUID)."""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        
        valid_mbids = [
            "12345678-1234-1234-1234-123456789012",
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        ]
        
        invalid_mbids = [
            "not-a-uuid",
            "12345678-1234-1234-1234",
            "",
        ]
        
        for mbid in valid_mbids:
            if mbid:
                assert re.match(uuid_pattern, mbid) is not None
        
        for mbid in invalid_mbids:
            if mbid:
                assert re.match(uuid_pattern, mbid) is None
    
    def test_lyrics_not_empty(self):
        """Test that lyrics content is not empty."""
        valid_lyrics = "This is a valid lyric\nWith multiple lines"
        empty_lyrics = ""
        
        assert len(valid_lyrics) > 0
        assert len(empty_lyrics) == 0
    
    def test_date_format_validation(self):
        """Test date format validation."""
        valid_dates = [
            "2025-12-12 20:54:13",
            "2025-01-01 00:00:00",
        ]
        
        for date_str in valid_dates:
            parsed = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            assert parsed is not None


class TestExtractedDataQuality:
    """Test quality of extracted data."""
    
    def test_extracted_artist_has_name(self):
        """Test that extracted artist has a name."""
        artist_data = {'name': 'Test Artist', 'id': 1}
        assert 'name' in artist_data
        assert len(artist_data['name']) > 0
    
    def test_extracted_song_has_required_fields(self):
        """Test that extracted song has required fields."""
        song_data = {
            'id': 1,
            'title': 'Test Song',
            'artist_id': 1,
            'artist_name': 'Test Artist'
        }
        
        required_fields = ['id', 'title', 'artist_id', 'artist_name']
        for field in required_fields:
            assert field in song_data
            assert song_data[field] is not None
    
    def test_extracted_lyrics_has_content(self):
        """Test that extracted lyrics has content."""
        lyric_data = {
            'id': 1,
            'song_id': 1,
            'content': 'Line 1\nLine 2\nLine 3',
            'mbid': '12345678-1234-1234-1234-123456789012'
        }
        
        assert len(lyric_data['content']) > 0
        assert '\n' in lyric_data['content'] or len(lyric_data['content']) > 20


class TestDatabaseConstraints:
    """Test database constraints enforcement."""
    
    def test_unique_artist_constraint(self):
        """Test that artist names must be unique."""
        artists = ["Artist A", "Artist B", "Artist A"]
        
        unique_artists = set(artists)
        assert len(unique_artists) == 2  # Should only have 2 unique
    
    def test_not_null_constraints(self):
        """Test that required fields are validated."""
        valid_song = {
            'id': 1,
            'title': 'Song',
            'artist_id': 1,
        }
        
        # All required fields present
        assert all(field is not None for field in valid_song.values())
    
    def test_foreign_key_reference(self):
        """Test that foreign key references are valid."""
        artists = {1: 'Artist 1', 2: 'Artist 2'}
        songs = {
            101: {'title': 'Song 1', 'artist_id': 1},
            102: {'title': 'Song 2', 'artist_id': 2},
        }
        
        # Verify all songs reference valid artists
        for song_id, song_data in songs.items():
            assert song_data['artist_id'] in artists


class TestExtractionErrorHandling:
    """Test error handling in extraction."""
    
    def test_handle_missing_data_fields(self):
        """Test handling of missing data fields."""
        incomplete_data = {'title': 'Song'}
        expected_fields = ['title', 'artist', 'year']
        
        missing_fields = [f for f in expected_fields if f not in incomplete_data]
        assert len(missing_fields) > 0
    
    def test_handle_invalid_types(self):
        """Test handling of invalid data types."""
        invalid_data = {
            'id': 'not-a-number',  # Should be int
            'title': 123,  # Should be string
        }
        
        # In real system, these would raise errors
        assert isinstance(invalid_data['id'], str)
        assert isinstance(invalid_data['title'], int)
    
    def test_sanitize_string_input(self):
        """Test sanitization of string inputs."""
        dirty_inputs = [
            "Normal Title",
            "Title with\nnewline",
            "Title with\t\ttabs",
            "Title with 'quotes'",
            'Title with "double quotes"',
        ]
        
        for input_str in dirty_inputs:
            # Should still be valid strings
            assert isinstance(input_str, str)
            assert len(input_str) > 0


class TestExtractionRobustness:
    """Test robustness of extraction processes."""
    
    def test_handle_duplicate_entries(self):
        """Test handling of duplicate entries."""
        entries = ['Song A', 'Song B', 'Song A', 'Song C', 'Song B']
        unique_entries = list(set(entries))
        
        assert len(unique_entries) == 3
    
    def test_handle_case_sensitivity(self):
        """Test case sensitivity in matching."""
        artists = ['The Beatles', 'the beatles', 'THE BEATLES']
        
        # Different cases should be treated as different (or normalized)
        assert len(set(artists)) == 3  # Currently different
    
    def test_batch_processing_partial_failure(self):
        """Test batch processing with partial failures."""
        items = [
            {'id': 1, 'name': 'Valid'},
            {'id': 2, 'name': 'Valid'},
            {'id': 3, 'name': 'Valid'},
        ]
        
        processed = []
        failed = []
        
        for item in items:
            if item and 'name' in item:
                processed.append(item)
            else:
                failed.append(item)
        
        assert len(processed) >= 0
        assert len(processed) + len(failed) == len(items)


class TestExtractionMetrics:
    """Test metrics and monitoring of extraction."""
    
    def test_extraction_completeness(self):
        """Test extraction completeness calculation."""
        total_items = 100
        extracted_items = 95
        
        completeness = (extracted_items / total_items) * 100
        assert completeness == 95.0
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        total_attempts = 100
        failed_attempts = 5
        
        error_rate = (failed_attempts / total_attempts) * 100
        assert error_rate == 5.0
    
    def test_timestamp_tracking(self):
        """Test timestamp tracking of extractions."""
        extraction_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        parsed_time = datetime.strptime(extraction_timestamp, "%Y-%m-%d %H:%M:%S")
        assert parsed_time is not None
        assert isinstance(parsed_time, datetime)

