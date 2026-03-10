"""
Email Service - Resend Integration

World-class email templates designed for maximum conversion.
No AI slop. Professional, clean, genuinely valuable.

Design Principles:
- Clean typography (system fonts, proper hierarchy)
- Generous whitespace (32px+ padding)
- Strategic color use (navy primary, teal accent)
- No emoji spam (1-2 max per email)
- Clear value proposition
- Blurred data that creates curiosity, not frustration
- Strong, single CTA per email
- Mobile-responsive tables
"""

import requests
from typing import Optional, Dict
from datetime import datetime
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        self.base_url = "https://api.resend.com/emails"
        
        if not self.api_key:
            print("⚠️  RESEND_API_KEY not configured - emails will print to console")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send an email via Resend"""
        
        if settings.DEBUG or not self.api_key:
            print(f"\n📧 EMAIL (DEV MODE)")
            print(f"To: {to}")
            print(f"Subject: {subject}")
            print(f"From: {self.from_name} <{self.from_email}>")
            print()
            return True
        
        try:
            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                payload["text"] = text_content
            
            if reply_to:
                payload["reply_to"] = reply_to
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Email sent to {to}")
                return True
            else:
                print(f"❌ Resend API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    # ========== SALARY CHECK TEASER (FREE → CAREER) ==========
    
    def send_salary_check_teaser(self, to: str, data: Dict) -> bool:
        """
        Salary check teaser for FREE users.
        Design: Clean, professional, creates genuine curiosity.
        """
        subject = "Your Q1 salary check is ready"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Quarterly Salary Check</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">Your Q1 2026 Salary Check</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #334155;">Hi {data.get('user_name', 'there')},</p>
                            
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                It's time for your quarterly salary check. We've analyzed market data for your role and location.
                            </p>
                            
                            <!-- Current Salary -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Your Current Salary</p>
                                <p style="margin: 0; font-size: 42px; font-weight: 700; color: #0f172a; line-height: 1;">£{data.get('current_salary', 0):,}</p>
                            </div>
                            
                            <!-- Market Data (Blurred) -->
                            <div style="background-color: #fafafa; border: 1px solid #e2e8f0; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 24px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Market Benchmark</p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%" style="padding-bottom: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #94a3b8;">Market Average</p>
                                            <p style="margin: 0; font-size: 24px; font-weight: 600; color: #cbd5e1;">Available with CAREER</p>
                                        </td>
                                        <td width="50%" style="padding-bottom: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #94a3b8;">Top 25%</p>
                                            <p style="margin: 0; font-size: 24px; font-weight: 600; color: #cbd5e1;">Available with CAREER</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2">
                                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #94a3b8;">Similar Roles</p>
                                            <p style="margin: 0; font-size: 16px; color: #475569;">{data.get('similar_roles_count', 3)} roles with salary data</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Insight -->
                            <div style="background-color: #fffbeb; border-left: 3px solid #f59e0b; padding: 20px 24px; margin-bottom: 32px;">
                                <p style="margin: 0; font-size: 15px; color: #92400e;">
                                    <strong>Preliminary analysis:</strong> {data.get('hint_text', 'Market comparison available with full report')}
                                </p>
                            </div>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('upgrade_url', '/billing/upgrade?plan=career')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            View full salary report
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Value Props -->
                            <div style="border-top: 1px solid #e2e8f0; padding-top: 32px;">
                                <p style="margin: 0 0 16px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">CAREER includes:</p>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%" style="padding-bottom: 12px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ 4 salary checks per year</p>
                                        </td>
                                        <td width="50%" style="padding-bottom: 12px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ Full market benchmarks</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td width="50%" style="padding-bottom: 12px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ Similar roles with salaries</p>
                                        </td>
                                        <td width="50%" style="padding-bottom: 12px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ Promotion alerts</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td width="50%">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ Passive job alerts</p>
                                        </td>
                                        <td width="50%">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">✓ Annual career report</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <p style="margin: 32px 0 0 0; font-size: 14px; color: #64748b;">
                                {data.get('monthly_equivalent', '$12.42')}/month when billed annually
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== SALARY CHECK FULL (PRO/CAREER) ==========
    
    def send_salary_check_full(self, to: str, data: Dict) -> bool:
        """
        Full salary check for paid users.
        Design: Clean data visualization, actionable insights.
        """
        is_below = data.get('underpaid_percentage', 0) > 0
        subject = "Your salary is competitive" if not is_below else f"Action needed: You're {data.get('underpaid_percentage', 0):.0f}% below market"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: {'#dc2626' if is_below else '#16a34a'}; text-transform: uppercase; letter-spacing: 0.5px;">
                                {'Market Alert' if is_below else 'Quarterly Check Complete'}
                            </p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">
                                {'Your salary is below market average' if is_below else 'Your salary is competitive'}
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                Here's how your compensation compares to the market for your role, location, and experience level.
                            </p>
                            
                            <!-- Salary Comparison -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="50%" style="padding-right: 16px;">
                                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Your Salary</p>
                                            <p style="margin: 0; font-size: 36px; font-weight: 700; color: #0f172a;">£{data.get('current_salary', 0):,}</p>
                                        </div>
                                    </td>
                                    <td width="50%" style="padding-left: 16px;">
                                        <div style="background-color: {'#fef2f2' if is_below else '#f0fdf4'}; border: 1px solid {'#fecaca' if is_below else '#bbf7d0'}; padding: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Market Average</p>
                                            <p style="margin: 0; font-size: 36px; font-weight: 700; color: {'#dc2626' if is_below else '#16a34a'};">£{data.get('market_avg', 0):,}</p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Difference -->
                            {f'''
                            <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 24px; margin-bottom: 32px;">
                                <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 600; color: #dc2626;">You're underpaid by {data.get('underpaid_percentage', 0):.0f}%</p>
                                <p style="margin: 0; font-size: 15px; color: #991b1b;">That's £{data.get('market_avg', 0) - data.get('current_salary', 0):,} less than market average per year</p>
                            </div>
                            ''' if is_below else ''}
                            
                            <!-- Percentile -->
                            <div style="margin-bottom: 32px;">
                                <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #334155;">Market Position</p>
                                <div style="background-color: #e2e8f0; height: 8px; margin-bottom: 8px;">
                                    <div style="background-color: #0f172a; width: {data.get('percentile', 50)}%; height: 100%;"></div>
                                </div>
                                <p style="margin: 0; font-size: 14px; color: #64748b;">You're in the top {data.get('percentile', 50)}% of earners for your role</p>
                            </div>
                            
                            <!-- Benchmarks -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="50%" style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 4px 0; font-size: 13px; color: #64748b;">Top 25%</p>
                                        <p style="margin: 0; font-size: 20px; font-weight: 700; color: #0f172a;">£{data.get('market_top_25', 0):,}</p>
                                    </td>
                                    <td width="50%" style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 4px 0; font-size: 13px; color: #64748b;">Top 10%</p>
                                        <p style="margin: 0; font-size: 20px; font-weight: 700; color: #0f172a;">£{data.get('market_top_10', 0):,}</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}/career?tab=salary" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            View detailed analysis
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 32px 0 0 0; font-size: 14px; color: #64748b;">
                                Next review: {data.get('next_review_date', 'Q2 2026')}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== PROMOTION READINESS TEASER (PRO → CAREER) ==========
    
    def send_promotion_readiness_teaser(self, to: str, data: Dict) -> bool:
        """
        Promotion readiness teaser for PRO users.
        Design: Celebrates achievement, shows opportunity exists, blurs salary.
        """
        subject = f"You're ready for a {data.get('next_level', 'Senior')} role"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #7c3aed; text-transform: uppercase; letter-spacing: 0.5px;">Career Milestone</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">You're ready for a {data.get('next_level', 'Senior')} role</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                Based on your experience, skills, and leadership, you've reached a major career milestone.
                            </p>
                            
                            <!-- Readiness Score -->
                            <div style="background-color: #f5f3ff; border: 1px solid #e9d5ff; padding: 32px; text-align: center; margin-bottom: 32px;">
                                <p style="margin: 0 0 16px 0; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Promotion Readiness Score</p>
                                <p style="margin: 0; font-size: 64px; font-weight: 800; color: #7c3aed; line-height: 1;">{data.get('score', 85)}</p>
                                <p style="margin: 8px 0 0 0; font-size: 14px; color: #6b7280;">out of 100</p>
                            </div>
                            
                            <!-- Profile Breakdown -->
                            <div style="margin-bottom: 32px;">
                                <p style="margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #334155;">Your Profile</p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td colspan="2" style="padding-bottom: 8px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">{data.get('months_in_role', 20)} months tenure</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="padding-bottom: 8px;">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">{data.get('skills_gained', 5)} skills gained</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2">
                                            <p style="margin: 0; font-size: 15px; color: #334155;">{data.get('leadership_count', 2)} leadership projects</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Opportunity (Blurred) -->
                            <div style="background-color: #fafafa; border: 1px solid #e2e8f0; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 24px 0; font-size: 14px; font-weight: 600; color: #334155;">Market Opportunity</p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%" style="padding-bottom: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #64748b;">Available Roles</p>
                                            <p style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a;">{data.get('roles_count', 847)}</p>
                                        </td>
                                        <td width="50%" style="padding-bottom: 24px;">
                                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #64748b;">Average Salary</p>
                                            <p style="margin: 0; font-size: 24px; font-weight: 600; color: #94a3b8;">Available with CAREER</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('upgrade_url', '/billing/upgrade?plan=career')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            See salary opportunities
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0; font-size: 14px; color: #64748b;">
                                Don't leave money on the table. See what you're worth.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== PROMOTION READINESS FULL (CAREER) ==========
    
    def send_promotion_readiness_full(self, to: str, data: Dict) -> bool:
        """
        Full promotion readiness for CAREER users.
        Design: Shows full opportunity, clear action path.
        """
        subject = f"You're ready for a {data.get('next_level', 'Senior')} role"
        
        increase = data.get('potential_increase', 0)
        increase_pct = (increase / data.get('current_salary', 1) * 100) if data.get('current_salary') else 0
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Market Opportunity</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">Your next role is worth +£{increase:,}</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                You've earned this. Based on your experience and skills, here's your market opportunity.
                            </p>
                            
                            <!-- Opportunity Card -->
                            <div style="background-color: #0f172a; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Market Opportunity</p>
                                <p style="margin: 0 0 24px 0; font-size: 48px; font-weight: 800; color: #14b8a6; line-height: 1;">+£{increase:,}</p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%">
                                            <p style="margin: 0 0 4px 0; font-size: 13px; color: #64748b;">Current</p>
                                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: #ffffff;">£{data.get('current_salary', 0):,}</p>
                                        </td>
                                        <td width="50%">
                                            <p style="margin: 0 0 4px 0; font-size: 13px; color: #64748b;">Market Rate</p>
                                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: #14b8a6;">£{data.get('market_salary', 0):,}</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Stats -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="50%" style="padding: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 4px 0; font-size: 32px; font-weight: 800; color: #0f172a;">{data.get('roles_count', 847)}</p>
                                        <p style="margin: 0; font-size: 14px; color: #64748b;">Available roles</p>
                                    </td>
                                    <td width="50%" style="padding: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 4px 0; font-size: 32px; font-weight: 800; color: #059669;">{data.get('score', 85)}</p>
                                        <p style="margin: 0; font-size: 14px; color: #64748b;">Readiness score</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTAs -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}/career?tab=jobs" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; margin-right: 12px; border-radius: 0;">
                                            See available roles
                                        </a>
                                        <a href="{settings.FRONTEND_URL}/career?tab=prep" style="display: inline-block; background-color: #ffffff; color: #0f172a; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border: 1px solid #e2e8f0; border-radius: 0;">
                                            Interview prep
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== NETWORK FOMO (FREE) ==========
    
    def send_network_fomo(self, to: str, data: Dict) -> bool:
        """
        Network FOMO for FREE users.
        Design: Social proof without being manipulative.
        """
        subject = "Career movements in your network"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #ea580c; text-transform: uppercase; letter-spacing: 0.5px;">Industry Insights</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">Career movements in {data.get('location', 'your area')}</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                We track anonymized career data to help you understand market trends. Here's what's happening in your network.
                            </p>
                            
                            <!-- Stats -->
                            <div style="background-color: #fffbeb; border: 1px solid #fde68a; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #92400e; text-transform: uppercase; letter-spacing: 0.5px;">Average Increase</p>
                                <p style="margin: 0; font-size: 48px; font-weight: 800; color: #92400e; line-height: 1;">+{data.get('avg_increase_pct', 31)}%</p>
                                <p style="margin: 8px 0 0 0; font-size: 15px; color: #78350f;">£{data.get('avg_increase_amount', 24000):,} for recent promotions</p>
                            </div>
                            
                            <!-- Recent Promotions -->
                            <div style="margin-bottom: 32px;">
                                <p style="margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #334155;">Recent Promotions</p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td>
                                                        <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 600; color: #0f172a;">John D.</p>
                                                        <p style="margin: 0; font-size: 14px; color: #64748b;">SWE → Senior</p>
                                                    </td>
                                                    <td align="right">
                                                        <p style="margin: 0; font-size: 15px; font-weight: 700; color: #16a34a;">+£28k</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td>
                                                        <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 600; color: #0f172a;">Sarah M.</p>
                                                        <p style="margin: 0; font-size: 14px; color: #64748b;">Mid → Lead</p>
                                                    </td>
                                                    <td align="right">
                                                        <p style="margin: 0; font-size: 15px; font-weight: 700; color: #16a34a;">+£35k</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td>
                                                        <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 600; color: #0f172a;">Mike R.</p>
                                                        <p style="margin: 0; font-size: 14px; color: #64748b;">SWE → Staff</p>
                                                    </td>
                                                    <td align="right">
                                                        <p style="margin: 0; font-size: 15px; font-weight: 700; color: #16a34a;">+£42k</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('upgrade_url', '/billing/upgrade')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            See how they did it
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0; font-size: 14px; color: #64748b;">
                                Understanding market trends helps you make better career decisions.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== QUARTERLY REVIEW TEASER (FREE) ==========
    
    def send_quarterly_review_teaser(self, to: str, data: Dict) -> bool:
        """Quarterly review teaser for FREE users."""
        subject = "Time for your quarterly review"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">Time for your quarterly review</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                It's been {data.get('months_since_start', 3)} months. Here's how your plan compares to what CAREER offers.
                            </p>
                            
                            <!-- Comparison -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="50%" style="padding: 24px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 16px 0; font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">FREE</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #dc2626;">✕ 1 salary check/year</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #dc2626;">✕ Basic market data</p>
                                        <p style="margin: 0; font-size: 15px; color: #dc2626;">✕ No promotion alerts</p>
                                    </td>
                                    <td width="50%" style="padding: 24px; background-color: #f0fdf4; border: 1px solid #86efac;">
                                        <p style="margin: 0 0 16px 0; font-size: 13px; font-weight: 600; color: #166534; text-transform: uppercase; letter-spacing: 0.5px;">CAREER</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #166534;">✓ 4 salary checks/year</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #166534;">✓ Full market benchmarks</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #166534;">✓ Promotion alerts</p>
                                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #166534;">✓ Passive job alerts</p>
                                        <p style="margin: 0; font-size: 15px; color: #166534;">✓ Annual career report</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Special Offer -->
                            <div style="background-color: #fffbeb; border: 1px solid #fde68a; padding: 24px; margin-bottom: 32px;">
                                <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #92400e; text-transform: uppercase; letter-spacing: 0.5px;">Special Offer</p>
                                <p style="margin: 0; font-size: 32px; font-weight: 800; color: #92400e;">{data.get('special_offer', '$99 first year')}</p>
                                <p style="margin: 8px 0 0 0; font-size: 15px; color: #78350f;">Normally {data.get('regular_price', '$149/year')}</p>
                            </div>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('upgrade_url', '/billing/upgrade?plan=career')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            Upgrade to CAREER
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== ANNUAL REPORT TEASER (FREE) ==========
    
    def send_annual_report_teaser(self, to: str, data: Dict) -> bool:
        """Annual report teaser for FREE users."""
        subject = f"Your {data.get('year', 2025)} career report is ready"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #6366f1; text-transform: uppercase; letter-spacing: 0.5px;">Annual Summary</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">Your {data.get('year', 2025)} Career Report</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                Your year in review is ready. Here's a preview of your career summary.
                            </p>
                            
                            <!-- Summary -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="50%" style="padding: 24px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">Current Company</p>
                                        <p style="margin: 0; font-size: 20px; font-weight: 700; color: #0f172a;">{data.get('current_company', 'Your Company')}</p>
                                    </td>
                                    <td width="50%" style="padding: 24px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">Current Salary</p>
                                        <p style="margin: 0; font-size: 20px; font-weight: 700; color: #0f172a;">{data.get('current_salary', '£XX,XXX')}</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Full Report (Blurred) -->
                            <div style="background-color: #fafafa; border: 1px solid #e2e8f0; padding: 32px; margin-bottom: 32px;">
                                <p style="margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #334155;">Full Report Includes</p>
                                <p style="margin: 0 0 12px 0; font-size: 15px; color: #64748b;">• Salary growth vs market</p>
                                <p style="margin: 0 0 12px 0; font-size: 15px; color: #64748b;">• Promotion timeline analysis</p>
                                <p style="margin: 0 0 12px 0; font-size: 15px; color: #64748b;">• Skills gap analysis</p>
                                <p style="margin: 0 0 12px 0; font-size: 15px; color: #64748b;">• 2026 career projections</p>
                                <p style="margin: 0; font-size: 15px; color: #64748b;">• Shareable PDF for LinkedIn</p>
                            </div>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('upgrade_url', '/billing/upgrade?plan=career')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            Unlock full report
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
    
    # ========== PASSIVE ALERTS (CAREER) ==========
    
    def send_passive_alerts(self, to: str, data: Dict) -> bool:
        """Passive job alerts for CAREER users."""
        subject = f"{len(data.get('jobs', []))} opportunities this week"
        
        jobs_html = ""
        for job in data.get('jobs', []):
            jobs_html += f"""
            <tr>
                <td style="padding: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td>
                                <p style="margin: 0 0 4px 0; font-size: 16px; font-weight: 700; color: #0f172a;">{job.get('title', 'Role')}</p>
                                <p style="margin: 0; font-size: 14px; color: #64748b;">{job.get('company', 'Company')}</p>
                            </td>
                            <td align="right">
                                <p style="margin: 0; font-size: 18px; font-weight: 700; color: #16a34a;">£{job.get('salary', 0):,}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #0f172a; line-height: 1.6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9;">
        <tr>
            <td align="center" style="padding: 48px 24px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 48px 48px 32px 48px; border-bottom: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Curated Opportunities</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.2;">{len(data.get('jobs', []))} roles this week</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 48px;">
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #334155;">
                                Only roles 20%+ better than your current £{data.get('current_salary', 0):,}. Quality over quantity.
                            </p>
                            
                            <!-- Jobs -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                                {jobs_html}
                            </table>
                            
                            <!-- CTA -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <a href="{settings.FRONTEND_URL}{data.get('cta_url', '/dashboard?tab=jobs')}" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 16px 40px; font-size: 15px; font-weight: 600; border-radius: 0;">
                                            View all opportunities
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 32px 0 0 0; font-size: 14px; color: #64748b;">
                                We only send roles that are genuinely better than your current position.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 48px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">JobScale · Career Intelligence Platform</p>
                            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                                <a href="{settings.FRONTEND_URL}/settings/notifications" style="color: #64748b; text-decoration: underline;">Manage email preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to, subject, html)
