"""
Smart Microgrid Manager Pro - Branding Module
Contains company branding, logos, and theming utilities.
"""

from datetime import datetime
from typing import Dict, Optional

# SVG Logo as inline string for easy integration
SVG_LOGO = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="95" fill="#1A365D" stroke="#48BB78" stroke-width="4"/>
  
  <circle cx="100" cy="80" r="15" fill="#ED8936" />
  <g stroke="#ED8936" stroke-width="2">
    <line x1="100" y1="55" x2="100" y2="65" />
    <line x1="100" y1="95" x2="100" y2="105" />
    <line x1="75" y1="80" x2="85" y2="80" />
    <line x1="115" y1="80" x2="125" y2="80" />
  </g>

  <line x1="100" y1="80" x2="100" y2="110" stroke="#ffffff" stroke-width="3" />
  <path d="M100 80 L85 70 L100 75 L115 70 Z" fill="#ffffff" />

  <g stroke="#48BB78" stroke-width="2" fill="none">
    <path d="M100 110 L100 140" />
    <path d="M100 120 L80 140" />
    <path d="M100 120 L120 140" />
    <circle cx="100" cy="145" r="3" fill="#48BB78" />
    <circle cx="80" cy="145" r="3" fill="#48BB78" />
    <circle cx="120" cy="145" r="3" fill="#48BB78" />
  </g>

  <defs>
    <path id="textPath" d="M 20, 100 A 80, 80 0 1, 1 180, 100" />
  </defs>
  <text fill="white" font-family="Arial" font-size="12" font-weight="bold">
    <textPath href="#textPath" startOffset="50%" text-anchor="middle">
      OPTIMAL GRID SOLUTIONS
    </textPath>
  </text>
</svg>"""

# Smaller logo variant for headers
SVG_LOGO_SMALL = """<svg width="50" height="50" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="95" fill="#1A365D" stroke="#48BB78" stroke-width="4"/>
  <circle cx="100" cy="80" r="15" fill="#ED8936" />
  <g stroke="#ED8936" stroke-width="2">
    <line x1="100" y1="55" x2="100" y2="65" />
    <line x1="100" y1="95" x2="100" y2="105" />
    <line x1="75" y1="80" x2="85" y2="80" />
    <line x1="115" y1="80" x2="125" y2="80" />
  </g>
  <line x1="100" y1="80" x2="100" y2="110" stroke="#ffffff" stroke-width="3" />
  <path d="M100 80 L85 70 L100 75 L115 70 Z" fill="#ffffff" />
  <g stroke="#48BB78" stroke-width="2" fill="none">
    <path d="M100 110 L100 140" />
    <path d="M100 120 L80 140" />
    <path d="M100 120 L120 140" />
    <circle cx="100" cy="145" r="3" fill="#48BB78" />
    <circle cx="80" cy="145" r="3" fill="#48BB78" />
    <circle cx="120" cy="145" r="3" fill="#48BB78" />
  </g>
</svg>"""

# Company Branding Settings
COMPANY_BRANDING = {
    'company_name': 'OPTIMAL GRID SOLUTIONS',
    'tagline': 'Smart Microgrid Management',
    'logo_svg': SVG_LOGO,
    'logo_svg_small': SVG_LOGO_SMALL,
    'primary_color': '#1A365D',
    'secondary_color': '#48BB78',
    'accent_color': '#ED8936',
    'report_title': 'Energy Optimization Report',
    'footer_text': 'Powered by Optimal Grid Solutions',
    'website': 'https://optimalgridsolutions.com',
    'contact_email': 'contact@optimalgridsolutions.com',
    'include_timestamp': True
}


def get_logo_html(size: str = 'medium') -> str:
    """Get the SVG logo as HTML string.
    
    Args:
        size: 'small', 'medium', or 'large'
    
    Returns:
        SVG logo as HTML string
    """
    size_map = {
        'small': (50, 50),
        'medium': (100, 100),
        'large': (200, 200)
    }
    width, height = size_map.get(size, (100, 100))
    
    return f'<svg width="{width}" height="{height}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">{SVG_LOGO.split(">")[1]}</svg>'


def get_header_html(title: str = None, subtitle: str = None) -> str:
    """Generate a branded header with logo and text.
    
    Args:
        title: Main title (defaults to company name)
        subtitle: Subtitle text
    
    Returns:
        HTML header string
    """
    title = title or COMPANY_BRANDING['company_name']
    subtitle = subtitle or COMPANY_BRANDING['tagline']
    
    return f"""
<div style="display: flex; align-items: center; gap: 20px; padding: 20px; background: linear-gradient(135deg, #1A365D, #2D4A77); border-radius: 10px; margin-bottom: 20px;">
    <div style="flex-shrink: 0;">
        {SVG_LOGO_SMALL}
    </div>
    <div>
        <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">{title}</h1>
        <p style="margin: 5px 0 0 0; color: #48BB78; font-size: 14px;">{subtitle}</p>
    </div>
</div>
"""


def get_footer_html() -> str:
    """Generate a branded footer.
    
    Returns:
        HTML footer string
    """
    return f"""
<div style="text-align: center; padding: 20px; margin-top: 30px; border-top: 2px solid #48BB78; color: #1A365D;">
    <p style="margin: 5px 0;">
        <strong>{COMPANY_BRANDING['company_name']}</strong> | {COMPANY_BRANDING['footer_text']}
    </p>
    <p style="margin: 5px 0; font-size: 12px; color: #666;">
        {COMPANY_BRANDING['website']} | {COMPANY_BRANDING['contact_email']}
    </p>
    <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </p>
</div>
"""


def get_branding_css() -> str:
    """Get CSS styles for branding.
    
    Returns:
        CSS styles as string
    """
    return """
<style>
    .brand-header {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px;
        background: linear-gradient(135deg, #1A365D, #2D4A77);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .brand-title {
        color: #ffffff;
        font-size: 28px;
        font-weight: bold;
        margin: 0;
    }
    .brand-subtitle {
        color: #48BB78;
        font-size: 14px;
        margin: 5px 0 0 0;
    }
    .brand-logo {
        flex-shrink: 0;
    }
    .brand-footer {
        text-align: center;
        padding: 20px;
        margin-top: 30px;
        border-top: 2px solid #48BB78;
        color: #1A365D;
    }
    .brand-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #48BB78;
    }
    .brand-button {
        background: linear-gradient(135deg, #1A365D, #2D4A77);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .brand-button:hover {
        background: linear-gradient(135deg, #2D4A77, #1A365D);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .brand-metric {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .brand-metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1A365D;
    }
    .brand-metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
</style>
"""


def set_branding(branding: Dict) -> None:
    """Update company branding settings.
    
    Args:
        branding: Dictionary with branding options to update
    """
    COMPANY_BRANDING.update(branding)


def get_company_info() -> Dict:
    """Get company information.
    
    Returns:
        Dictionary with company information
    """
    return COMPANY_BRANDING.copy()


def create_login_branding() -> str:
    """Generate HTML for login page branding.
    
    Returns:
        HTML string for login branding
    """
    return f"""
<div style="text-align: center; margin-bottom: 30px;">
    <div style="display: inline-block; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 15px;">
        {SVG_LOGO}
    </div>
    <h2 style="color: #1A365D; margin: 20px 0 10px 0; font-size: 28px; font-weight: bold;">
        {COMPANY_BRANDING['company_name']}
    </h2>
    <p style="color: #48BB78; margin: 0; font-size: 16px;">
        {COMPANY_BRANDING['tagline']}
    </p>
</div>
"""


def get_report_header(title: str = None) -> str:
    """Generate report header with logo.
    
    Args:
        title: Report title (optional)
    
    Returns:
        HTML report header
    """
    report_title = title or COMPANY_BRANDING['report_title']
    
    return f"""
<div style="display: flex; align-items: center; justify-content: space-between; padding: 30px; background: linear-gradient(135deg, #1A365D 0%, #2D4A77 100%); border-radius: 10px 10px 0 0;">
    <div>
        <h1 style="color: #ffffff; margin: 0; font-size: 24px;">{COMPANY_BRANDING['company_name']}</h1>
        <p style="color: #48BB78; margin: 5px 0 0 0; font-size: 14px;">{report_title}</p>
    </div>
    <div>
        {SVG_LOGO_SMALL}
    </div>
</div>
"""

