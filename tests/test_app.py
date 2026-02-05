"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test to ensure test isolation"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball practice and games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and compete in matches",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["lucas@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "noah@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Thursdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["grace@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and critical thinking skills",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["william@mergington.edu", "chloe@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["james@mergington.edu"]
        }
    }
    
    # Replace the app's activities with the original state
    from app import activities
    activities.clear()
    activities.update(original_activities)
    
    yield


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_contain_required_fields(self, client):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, activity in activities.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_contains_participants(self, client):
        """Test that activities contain their participants"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student(self, client):
        """Test that a student cannot signup twice"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test signup when activity is full"""
        # Get Tennis Club which has max 10 participants and only 1 current
        # Add 9 more to fill it
        for i in range(9):
            client.post(f"/activities/Tennis Club/signup?email=student{i}@mergington.edu")
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/Tennis Club/signup?email=student_extra@mergington.edu"
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]

    def test_signup_multiple_students(self, client):
        """Test multiple students can signup for the same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(f"/activities/Art Studio/signup?email={email1}")
        response2 = client.post(f"/activities/Art Studio/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert email1 in activities["Art Studio"]["participants"]
        assert email2 in activities["Art Studio"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered_student(self, client):
        """Test unregister for a student not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_frees_up_spot(self, client):
        """Test that unregistering frees up a spot in a full activity"""
        # Fill Tennis Club (max 10, currently has 1)
        for i in range(9):
            client.post(f"/activities/Tennis Club/signup?email=student{i}@mergington.edu")
        
        # Verify it's full
        response = client.post(
            "/activities/Tennis Club/signup?email=student_extra@mergington.edu"
        )
        assert response.status_code == 400
        
        # Unregister someone
        client.delete("/activities/Tennis Club/unregister?email=lucas@mergington.edu")
        
        # Now should be able to signup
        response = client.post(
            "/activities/Tennis Club/signup?email=student_extra@mergington.edu"
        )
        assert response.status_code == 200

    def test_unregister_multiple_participants(self, client):
        """Test unregistering multiple participants from the same activity"""
        email1 = "michael@mergington.edu"
        email2 = "daniel@mergington.edu"
        
        response1 = client.delete(f"/activities/Chess Club/unregister?email={email1}")
        response2 = client.delete(f"/activities/Chess Club/unregister?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert email1 not in activities["Chess Club"]["participants"]
        assert email2 not in activities["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "integration@mergington.edu"
        
        # Signup
        signup_response = client.post(f"/activities/Drama Club/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        get_response = client.get("/activities")
        assert email in get_response.json()["Drama Club"]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/Drama Club/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        get_response = client.get("/activities")
        assert email not in get_response.json()["Drama Club"]["participants"]

    def test_participant_count_updates(self, client):
        """Test that participant counts update correctly"""
        email = "counttest@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Science Club"]["participants"])
        
        # Signup
        client.post(f"/activities/Science Club/signup?email={email}")
        response = client.get("/activities")
        new_count = len(response.json()["Science Club"]["participants"])
        assert new_count == initial_count + 1
        
        # Unregister
        client.delete(f"/activities/Science Club/unregister?email={email}")
        response = client.get("/activities")
        final_count = len(response.json()["Science Club"]["participants"])
        assert final_count == initial_count
