"""
Google Sheets integration module.
Handles reading configuration/universe and writing trade suggestions and state.
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os


class SheetsManager:
    """Manages Google Sheets operations for trading data."""
    
    def __init__(self, sheet_id, credentials_file='credentials.json'):
        """
        Initialize Sheets Manager.
        
        Args:
            sheet_id: Google Sheet ID
            credentials_file: Path to service account credentials JSON
        """
        self.sheet_id = sheet_id
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            credentials_file, scopes=scope
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(sheet_id)
    
    def get_universe(self):
        """
        Read trading universe from the 'Universe' worksheet.
        
        Returns:
            list: List of ticker symbols
        """
        try:
            worksheet = self.spreadsheet.worksheet('Universe')
            # Assume tickers are in column A, starting from row 2 (skip header)
            values = worksheet.col_values(1)[1:]  # Skip header
            # Filter out empty values
            tickers = [ticker.strip().upper() for ticker in values if ticker.strip()]
            return tickers
        except gspread.exceptions.WorksheetNotFound:
            print("Warning: 'Universe' worksheet not found. Returning empty list.")
            return []
    
    def write_trade_suggestions(self, suggestions_df):
        """
        Write trade suggestions to 'TradeSuggestions' worksheet.
        
        Args:
            suggestions_df: DataFrame with columns [Ticker, Action, Quantity, Price, Reason, Approved]
        """
        try:
            worksheet = self.spreadsheet.worksheet('TradeSuggestions')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title='TradeSuggestions',
                rows=1000,
                cols=10
            )
        
        # Clear existing content
        worksheet.clear()
        
        # Write header
        header = ['Ticker', 'Action', 'Quantity', 'Price', 'Reason', 'Approved', 'Timestamp']
        worksheet.append_row(header)
        
        # Write data
        for _, row in suggestions_df.iterrows():
            worksheet.append_row([
                row.get('Ticker', ''),
                row.get('Action', ''),
                str(row.get('Quantity', '')),
                str(row.get('Price', '')),
                row.get('Reason', ''),
                row.get('Approved', 'NO'),
                row.get('Timestamp', '')
            ])
    
    def get_approved_trades(self):
        """
        Read approved trades from 'TradeSuggestions' worksheet.
        
        Returns:
            pd.DataFrame: DataFrame with approved trades
        """
        try:
            worksheet = self.spreadsheet.worksheet('TradeSuggestions')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # Filter for approved trades (case-insensitive)
            # Convert to string and handle NaN/None values
            df['Approved'] = df['Approved'].astype(str)
            approved_df = df[df['Approved'].str.upper() == 'YES'].copy()
            return approved_df
        except gspread.exceptions.WorksheetNotFound:
            return pd.DataFrame()
    
    def get_state(self):
        """
        Read state data from 'State' worksheet.
        
        Returns:
            pd.DataFrame: DataFrame with state data including peaks
        """
        try:
            worksheet = self.spreadsheet.worksheet('State')
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except gspread.exceptions.WorksheetNotFound:
            return pd.DataFrame()
    
    def update_state(self, state_df):
        """
        Update state data in 'State' worksheet.
        
        Args:
            state_df: DataFrame with columns [Ticker, Position, EntryPrice, Peak, ATRStop, LastUpdated]
        """
        try:
            worksheet = self.spreadsheet.worksheet('State')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title='State',
                rows=1000,
                cols=10
            )
        
        # Clear existing content
        worksheet.clear()
        
        # Write header
        header = ['Ticker', 'Position', 'EntryPrice', 'Peak', 'ATRStop', 'LastUpdated']
        worksheet.append_row(header)
        
        # Write data
        for _, row in state_df.iterrows():
            worksheet.append_row([
                row.get('Ticker', ''),
                str(row.get('Position', '')),
                str(row.get('EntryPrice', '')),
                str(row.get('Peak', '')),
                str(row.get('ATRStop', '')),
                row.get('LastUpdated', '')
            ])
