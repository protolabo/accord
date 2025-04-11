import pandas as pd
import email
import re
import json
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm

class EnronEmailParser:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path, quoting=1)

        self.forward_pattern = re.compile(
            r'(?:'
            # Pattern 1: Format standard Enron
            r'-{20,}\s*Forwarded by\s+(.+?)\s+on\s+(.+?)\s*-{20,}\s*\n'
            r'(?:"?([^"]+)"?\s+<([^>]+)>)?\s*on\s+(.+?)\n'
            r'To:\s*(.+?)\n'
            r'(?:cc:\s*(.+?)\n)?'
            r'Subject:\s*(.+?)\n\n'
            r'|'
            # Pattern 2: Format alternatif
            r'From:\s*([^\n]+)\n'
            r'Sent:\s*([^\n]+)\n'
            r'To:\s*([^\n]+)\n'
            r'(?:Cc:\s*([^\n]+)\n)?'
            r'Subject:\s*FW:\s*([^\n]+)\n\n'
            r')',
            re.DOTALL
        )

    def clean_quoted_text(self, text: str) -> str:
        """Nettoie le texte"""
        lines = text.split('\n')
        cleaned_lines = [line.lstrip('>').lstrip() for line in lines]
        return '\n'.join(cleaned_lines)

    def parse_email_headers(self, headers_text: str) -> Dict[str, str]:
        """Parse les en-têtes d'email"""
        headers = {}
        header_patterns = {
            'message_id': r'Message-ID: <(.+?)>',
            'date': r'Date: (.+?)\n',
            'from': r'From: (.+?)\n',
            'to': r'To: (.+?)\n',
            'subject': r'Subject: (.+?)\n',
        }

        for field, pattern in header_patterns.items():
            match = re.search(pattern, headers_text)
            if match:
                headers[field] = match.group(1).strip()

        if 'date' in headers:
            try:
                dt = email.utils.parsedate_to_datetime(headers['date'])
                headers['date'] = dt.isoformat()
            except:
                pass

        return headers

    def extract_forward_info(self, content: str) -> Tuple[List[Dict], str]:
        forward_chain = []
        matches = list(self.forward_pattern.finditer(content))

        for match in matches:
            groups = match.groups()
            if groups[0]:  # Format Enron standard
                forward_info = {
                    'forwarded_by': groups[0].strip(),
                    'forward_date': groups[1].strip(),
                    'from_name': groups[2].strip() if groups[2] else None,
                    'from_email': groups[3].strip() if groups[3] else None,
                    'original_date': groups[4].strip(),
                    'to': groups[5].strip(),
                    'cc': groups[6].strip() if groups[6] else None,
                    'subject': groups[7].strip()
                }
            else:  # Format alternatif
                forward_info = {
                    'from': groups[8].strip(),
                    'date': groups[9].strip(),
                    'to': groups[10].strip(),
                    'cc': groups[11].strip() if groups[11] else None,
                    'subject': groups[12].strip()
                }
            forward_chain.append(forward_info)

        if matches:
            content = content[matches[-1].end():].strip()

        return forward_chain, content

    def parse_email_content(self, raw_content: str) -> Dict:
        """Parse le contenu d'email"""
        content = raw_content.replace('\\n', '\n').replace('\\"', '"')
        parts = content.split('\n\n', 1)
        headers_section = parts[0]
        body = parts[1] if len(parts) > 1 else ''

        metadata = self.parse_email_headers(headers_section)
        forward_chain, main_content = self.extract_forward_info(body)

        return {
            'metadata': metadata,
            'forward_chain': forward_chain,
            'body': self.clean_quoted_text(main_content).strip()
        }

    def process_dataset(self, output_path: str, max_emails: Optional[int] = None) -> None:
        """Traite le dataset avec barre de progression."""
        processed_emails = []
        df_subset = self.df.head(max_emails) if max_emails else self.df

        for _, row in tqdm(df_subset.iterrows(), total=len(df_subset), desc="Traitement des emails"):
            try:
                parsed_email = self.parse_email_content(row['message'])
                processed_emails.append(parsed_email)
            except Exception as e:
                print(f"Erreur lors du parsing d'un email: {str(e)}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_emails, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    parser = EnronEmailParser('data/emails.csv')
    parser.process_dataset('data/emails.json', max_emails=1000)