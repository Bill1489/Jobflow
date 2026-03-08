"""
CV Parser - Extract structured data from uploaded CVs (PDF/DOCX)
"""
import re
import os
from typing import Dict, List, Optional


class CVParser:
    """Parse uploaded CVs and extract structured data"""
    
    def __init__(self):
        pass
    
    async def parse_cv(self, file_path: str, file_type: str) -> Dict:
        """
        Parse uploaded CV and extract structured data
        
        Args:
            file_path: Path to uploaded file
            file_type: 'pdf' or 'docx'
            
        Returns:
            Dict with extracted CV data
        """
        if file_type == 'pdf':
            text = await self._extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            text = await self._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Parse text into structured data
        return self._parse_text(text)
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            return text
        except ImportError:
            # Fallback if PyMuPDF not installed
            return await self._extract_text_fallback(file_path)
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""
    
    async def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            # Fallback if python-docx not installed
            return await self._extract_text_fallback(file_path)
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""
    
    async def _extract_text_fallback(self, file_path: str) -> str:
        """Fallback text extraction (basic)"""
        # Try to read as plain text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""
    
    def _parse_text(self, text: str) -> Dict:
        """Parse CV text into structured data"""
        if not text:
            return {}
        
        # Clean text
        text = text.strip()
        
        # Extract sections
        return {
            "personal_info": self._extract_personal_info(text),
            "summary": self._extract_summary(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "skills": self._extract_skills(text),
            "certifications": self._extract_certifications(text),
            "raw_text": text[:5000]  # Store first 5000 chars for reference
        }
    
    def _extract_personal_info(self, text: str) -> Dict:
        """Extract name, email, phone, location, links"""
        info = {}
        
        # Email pattern
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, text)
        if email_match:
            info['email'] = email_match.group()
        
        # Phone patterns (UK, US, international)
        phone_patterns = [
            r'\+?44\s?\d{4}\s?\d{6}',  # UK
            r'\+?1\s?\d{3}\s?\d{3}\s?\d{4}',  # US
            r'\+?\d{1,3}\s?\d{3,4}\s?\d{3,4}\s?\d{4}',  # International
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                info['phone'] = phone_match.group()
                break
        
        # LinkedIn URL
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        if linkedin_match:
            info['linkedin_url'] = f"https://{linkedin_match.group()}"
        
        # Portfolio/website URL
        website_match = re.search(r'(?:https?://)?(?:www\.)?[\w-]+\.[a-z]{2,3}', text)
        if website_match:
            url = website_match.group()
            if not url.startswith('http'):
                url = f"https://{url}"
            if 'linkedin' not in url:
                info['portfolio_url'] = url
        
        # Name (usually first line, capitalized)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line:
                # Skip if it looks like an address or contains numbers
                if not re.search(r'\d', line) and len(line.split()) <= 4:
                    info['full_name'] = line
                    break
        
        # Location (look for city names)
        city_pattern = r'(London|Manchester|Birmingham|Leeds|Glasgow|Edinburgh|Liverpool|Bristol|New York|San Francisco|Los Angeles|Seattle|Boston|Austin|Berlin|Munich|Paris|Amsterdam|Toronto|Vancouver|Sydney|Melbourne)'
        city_match = re.search(city_pattern, text, re.IGNORECASE)
        if city_match:
            info['location'] = city_match.group()
        
        return info
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary/profile section"""
        # Look for summary section
        summary_patterns = [
            r'(?:PROFILE|SUMMARY|ABOUT|PROFESSIONAL SUMMARY)[:\s]+(.*?)(?=\n\s*\n|\n(?:EXPERIENCE|WORK|EMPLOYMENT|EDUCATION|SKILLS))',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no section found, return first paragraph (excluding name/contact)
        lines = text.split('\n')
        paragraphs = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 50:  # Likely a paragraph
                paragraphs.append(line)
                if len(paragraphs) >= 1:
                    break
        
        return paragraphs[0] if paragraphs else ""
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        # Look for experience section
        exp_section = self._extract_section(text, ['EXPERIENCE', 'WORK', 'EMPLOYMENT', 'PROFESSIONAL EXPERIENCE'])
        
        if not exp_section:
            return experience
        
        # Split by company/role patterns
        # Pattern: Role at Company (Date - Date)
        entries = re.split(r'\n(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:at|@)\s+[A-Z])', exp_section)
        
        for entry in entries[:5]:  # Max 5 most recent roles
            if not entry.strip():
                continue
            
            exp_entry = {}
            
            # Extract company
            company_match = re.search(r'(?:at|@)\s+([A-Z][\w\s]+)', entry)
            if company_match:
                exp_entry['company'] = company_match.group(1).strip()
            
            # Extract role
            role_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', entry)
            if role_match:
                exp_entry['role'] = role_match.group(1).strip()
            
            # Extract dates
            date_pattern = r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|Present|Current)'
            date_match = re.search(date_pattern, entry)
            if date_match:
                exp_entry['start_date'] = date_match.group(1)
                exp_entry['end_date'] = date_match.group(2)
            
            # Extract description (bullet points)
            bullets = re.findall(r'[•\-\*]\s*(.+)', entry)
            if bullets:
                exp_entry['description'] = '\n'.join([f"• {b.strip()}" for b in bullets[:5]])
            
            if exp_entry.get('company') or exp_entry.get('role'):
                experience.append(exp_entry)
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education"""
        education = []
        
        # Look for education section
        edu_section = self._extract_section(text, ['EDUCATION', 'QUALIFICATIONS', 'ACADEMIC'])
        
        if not edu_section:
            return education
        
        # Split by institution patterns
        entries = re.split(r'\n(?=[A-Z][\w\s]+(?:University|College|Institute))', edu_section)
        
        for entry in entries[:3]:  # Max 3 most recent
            if not entry.strip():
                continue
            
            edu_entry = {}
            
            # Extract institution
            inst_match = re.search(r'([A-Z][\w\s]+(?:University|College|Institute)[\w\s]*)', entry)
            if inst_match:
                edu_entry['institution'] = inst_match.group(1).strip()
            
            # Extract degree
            degree_match = re.search(r'((?:B\.?|M\.?|Ph\.?D|Doctorate|Bachelor|Master|Doctor)[\w\s\.]+)', entry, re.IGNORECASE)
            if degree_match:
                edu_entry['degree'] = degree_match.group(1).strip()
            
            # Extract year
            year_match = re.search(r'(\d{4})', entry)
            if year_match:
                edu_entry['graduation_year'] = year_match.group(1)
            
            if edu_entry.get('institution') or edu_entry.get('degree'):
                education.append(edu_entry)
        
        return education
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills"""
        skills = []
        
        # Look for skills section
        skills_section = self._extract_section(text, ['SKILLS', 'TECHNICAL SKILLS', 'CORE SKILLS', 'COMPETENCIES'])
        
        if skills_section:
            # Extract comma or newline separated skills
            skill_list = re.split(r'[,\n]', skills_section)
            for skill in skill_list:
                skill = skill.strip().strip('•\-\*')
                if skill and len(skill) < 50 and len(skill) > 1:
                    skills.append(skill)
        
        # Also look for skill-like patterns throughout CV
        if len(skills) < 5:
            # Common tech skills
            tech_skills = [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++', 'C#',
                'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'FastAPI',
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
                'Git', 'CI/CD', 'Agile', 'Scrum'
            ]
            
            for skill in tech_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    if skill not in skills:
                        skills.append(skill)
        
        return skills[:20]  # Max 20 skills
    
    def _extract_certifications(self, text: str) -> List[Dict]:
        """Extract certifications"""
        certifications = []
        
        # Look for certifications section
        cert_section = self._extract_section(text, ['CERTIFICATION', 'CERTIFICATES', 'LICENSES', 'CREDENTIALS'])
        
        if cert_section:
            # Extract certification entries
            entries = cert_section.split('\n')
            for entry in entries:
                if entry.strip() and len(entry.strip()) > 5:
                    certifications.append({
                        'name': entry.strip(),
                        'issuer': '',
                        'year': ''
                    })
        
        return certifications
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a specific section from CV text"""
        for section_name in section_names:
            pattern = rf'{section_name}[:\s]+(.*?)(?=\n\s*[A-Z][A-Z\s]+:|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def suggest_improvements(self, parsed_cv: Dict) -> List[str]:
        """Suggest improvements for parsed CV"""
        suggestions = []
        
        # Check for missing sections
        if not parsed_cv.get('personal_info', {}).get('email'):
            suggestions.append("Add your email address")
        
        if not parsed_cv.get('summary'):
            suggestions.append("Add a professional summary (we can generate one with AI)")
        
        if not parsed_cv.get('experience'):
            suggestions.append("Add your work experience")
        
        if len(parsed_cv.get('skills', [])) < 5:
            suggestions.append("Add more skills (aim for 10-15)")
        
        # Check experience quality
        for exp in parsed_cv.get('experience', []):
            desc = exp.get('description', '')
            if not desc:
                suggestions.append(f"Add details to your {exp.get('role', 'role')} position")
            elif len(desc) < 100:
                suggestions.append(f"Expand your {exp.get('role', 'role')} description with achievements")
            
            # Check for metrics
            if not re.search(r'\d+%|\d+x|£|\$|€', desc):
                suggestions.append("Add measurable achievements (numbers, percentages, impact)")
        
        # Check for action verbs
        action_verbs = ['Built', 'Led', 'Created', 'Reduced', 'Increased', 'Launched', 'Improved', 'Optimized']
        has_action_verbs = any(verb in parsed_cv.get('summary', '') for verb in action_verbs)
        if not has_action_verbs:
            suggestions.append("Use stronger action verbs (Built, Led, Created, etc.)")
        
        return suggestions


# Singleton instance
cv_parser = CVParser()
