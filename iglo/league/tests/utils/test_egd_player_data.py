from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase

from league.utils.egd import get_player_data_by_pin, EGDPlayerData, EGDException


class EGDPlayerDataTestCase(SimpleTestCase):
    
    def setUp(self):
        self.mock_success_response = MagicMock()
        self.mock_success_response.status_code = 200
        self.mock_success_response.json.return_value = {
            "retcode": "Ok",
            "Pin_Player": "12345678",
            "AGAID": "0",
            "Last_Name": "Smith",
            "Name": "John",
            "Country_Code": "PL",
            "Club": "Test",
            "Grade": "1d",
            "Grade_n": "30",
            "EGF_Placement": "500",
            "Gor": "2100",
            "DGor": "0",
            "Proposed_Grade": "0",
            "Tot_Tournaments": "50",
            "Last_Appearance": "G220101A",
            "Elab_Date": "2022-01-01",
            "Hidden_History": "0",
            "Real_Last_Name": "Smith",
            "Real_Name": "John"
        }
        
        self.mock_error_response = MagicMock()
        self.mock_error_response.status_code = 200
        self.mock_error_response.json.return_value = {
            "retcode": "Error",
            "error": "Invalid PIN"
        }
        
        self.mock_missing_gor_response = MagicMock()
        self.mock_missing_gor_response.status_code = 200
        self.mock_missing_gor_response.json.return_value = {
            "retcode": "Ok",
            "Pin_Player": "87654321",
            "Last_Name": "Doe",
            "Name": "Jane",
            "Country_Code": "US",
            # Missing Gor field
        }
        
        self.mock_http_error_response = MagicMock()
        self.mock_http_error_response.status_code = 404
    
    @patch('requests.get')
    def test_get_player_data_by_pin_success(self, mock_get):
        mock_get.return_value = self.mock_success_response
        
        result = get_player_data_by_pin("12345678")
        
        self.assertIsInstance(result, EGDPlayerData)
        self.assertEqual(result.pin, "12345678")
        self.assertEqual(result.first_name, "John")
        self.assertEqual(result.last_name, "Smith")
        self.assertEqual(result.country_code, "PL")
        self.assertEqual(result.club, "Test")
        self.assertEqual(result.grade, "1d")
        self.assertEqual(result.gor, 2100)
        self.assertEqual(result.last_appearance, "G220101A")
        self.assertEqual(result.total_tournaments, 50)
        self.assertEqual(result.egf_placement, 500)
    
    @patch('requests.get')
    def test_get_player_data_by_pin_error_response(self, mock_get):
        mock_get.return_value = self.mock_error_response
        
        with self.assertRaises(EGDException) as context:
            get_player_data_by_pin("invalid_pin")
        
        self.assertIn("EGD returned error", str(context.exception))
    
    @patch('requests.get')
    def test_get_player_data_by_pin_missing_gor(self, mock_get):
        mock_get.return_value = self.mock_missing_gor_response
        
        with self.assertRaises(EGDException) as context:
            get_player_data_by_pin("87654321")
        
        self.assertIn("Cannot parse player data", str(context.exception))
    
    @patch('requests.get')
    def test_get_player_data_by_pin_http_error(self, mock_get):
        mock_get.return_value = self.mock_http_error_response
        
        with self.assertRaises(EGDException) as context:
            get_player_data_by_pin("12345678")
        
        self.assertIn("EGD is responding with 404", str(context.exception))