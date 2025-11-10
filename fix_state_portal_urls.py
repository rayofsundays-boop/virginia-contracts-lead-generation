"""
Quick fix for most critical broken state portal URLs
Based on manual research of correct government procurement portals
"""

# Dictionary of corrections for broken URLs
URL_FIXES = {
    # Alabama - ALISON portal (broken)
    'https://alison.alabama.gov': 'https://alison.alabama.gov/ssw/r/bso$sso.startup',
    
    # Alaska - IRIS portal (broken)
    'https://iris-web.alaska.gov/webapp/PRDVSS1X1/AltSelfService': 'https://aws.state.ak.us/OnlinePublicNotices/default.aspx',
    
    # Arizona - procurement portal (404)
    'https://azscitech.com/Procurement': 'https://spo.az.gov/procurement',
    
    # Arkansas - DFA procurement (403)
    'https://www.dfa.arkansas.gov/offices/procurement/': 'https://www.dfa.arkansas.gov/procurement/',
    'https://www.arkansas.gov/purchasing': 'https://sai.arkansas.gov/purchasing/',
    
    # California - DGS opportunities (403)
    'https://www.dgs.ca.gov/PD/Opportunities': 'https://www.dgs.ca.gov/PD/About/Page-Content/PD-Branch-Intro-Accordion-List/Procurement-Division',
    
    # Delaware - OMB procurement (404)
    'https://gss.omb.delaware.gov/procurement/': 'https://gss.omb.delaware.gov/',
    
    # Georgia - GPR portal (405)
    'https://ssl.doas.state.ga.us/gpr/': 'https://doas.ga.gov/state-purchasing/vendor-resources',
    
    # Idaho - admin purchasing (404)
    'https://adm.idaho.gov/purchasing/': 'https://purchasing.idaho.gov/',
    
    # Illinois - Bids portal (timeout)
    'https://www.illinoisbids.com': 'https://www2.illinois.gov/cms/business/buy/Pages/bids.aspx',
    
    # Kansas - bid system (DNS error)
    'https://kansasbidsystem.ksgov.net': 'https://admin.ks.gov/offices/procurement-and-contracts/selling-to-the-state',
    
    # Kentucky - finance portal (403)
    'https://finance.ky.gov/services/statewidecontracting/Pages/default.aspx': 'https://eprocurement.ky.gov/epro/index.do',
    
    # Louisiana - OSP (404)
    'https://www.doa.la.gov/osp/': 'https://www.doa.la.gov/doa/osp/',
    
    # Maine - bids portal (404)
    'https://www.maine.gov/bids': 'https://www.maine.gov/dafs/bbm/procurementservices/upcoming-bids',
    
    # Maryland - eMD buyspeed (DNS error)
    'https://emaryland.buyspeed.com': 'https://buy.maryland.gov/',
    
    # Michigan - DTMB procurement (403)
    'https://www.michigan.gov/dtmb/procurement': 'https://www.michigan.gov/dtmb/procurement',
    'https://www.sigma.michigan.gov': 'https://www.michigan.gov/sigma',
    
    # Missouri - moBuy (DNS error)
    'https://www.moBuy.mo.gov': 'https://oa.mo.gov/purchasing/vendors',
    
    # Montana - marketplace (404/DNS)
    'https://gsd.mt.gov/About-Us/State-Procurement-Bureau': 'https://gsd.mt.gov/State-Procurement',
    'https://marketplace.mt.gov': 'https://gsd.mt.gov/State-Procurement/Bids-and-Contracts',
    
    # Nebraska - NEGP (DNS error)
    'https://www.negp.ne.gov': 'https://das.nebraska.gov/materiel/purchasing.html',
    
    # Nevada - purchasing (connection reset)
    'https://purchasing.nv.gov': 'https://purchasing.nv.gov/',
    
    # New Hampshire - DAS purchasing (403)
    'https://das.nh.gov/purchasing/': 'https://www.nh.gov/purchasing/',
    'https://www.nh.gov/purchasing/bids/': 'https://www.nh.gov/purchasing/bids.htm',
}

def apply_fixes():
    """Apply URL fixes to template"""
    import re
    
    template_path = 'templates/state_procurement_portals.html'
    
    # Read template
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Apply fixes
    fixes_applied = 0
    for old_url, new_url in URL_FIXES.items():
        if old_url in content:
            content = content.replace(f'href="{old_url}"', f'href="{new_url}"')
            fixes_applied += 1
            print(f'✓ Fixed: {old_url[:50]}... → {new_url[:50]}...')
    
    # Write back
    with open(template_path, 'w') as f:
        f.write(content)
    
    print(f'\n✅ Applied {fixes_applied} URL fixes to template')
    return fixes_applied

if __name__ == '__main__':
    print("=" * 80)
    print("STATE PROCUREMENT PORTALS - QUICK FIX")
    print("=" * 80)
    print(f"\nFixing {len(URL_FIXES)} broken URLs...\n")
    
    fixes_applied = apply_fixes()
    
    print("\n" + "=" * 80)
    print(f"COMPLETE - {fixes_applied} URLs updated")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Test the updated pages")
    print("2. Commit changes to git")
    print("3. Deploy to production")
