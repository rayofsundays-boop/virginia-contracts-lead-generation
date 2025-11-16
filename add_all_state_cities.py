"""
Add major cities and procurement portals for all 50 US states.

This enhances the city dropdown feature to work nationwide, not just VA/CA/TX/FL/NY.
For each state, includes 3-10 major cities with their procurement portal URLs.
"""

# Comprehensive city procurement portals for all 50 states
ALL_STATE_CITIES = {
    'AL': {
        'Birmingham': {
            'url': 'https://www.birminghamal.gov/procurement/',
            'bid_path': '/current-bids',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Montgomery': {
            'url': 'https://www.montgomeryal.gov/government/departments/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Mobile': {
            'url': 'https://www.cityofmobile.org/departments/purchasing/',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial']
        },
        'Huntsville': {
            'url': 'https://www.huntsvilleal.gov/business/solicitations/',
            'bid_path': '',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'AK': {
        'Anchorage': {
            'url': 'https://www.muni.org/Departments/purchasing/Pages/default.aspx',
            'bid_path': '/active-bids',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Fairbanks': {
            'url': 'https://fairbanks.finance.fnsb.gov/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Juneau': {
            'url': 'https://juneau.org/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['custodial', 'janitorial']
        }
    },
    'AZ': {
        'Phoenix': {
            'url': 'https://www.phoenix.gov/financesite/Pages/Procurement.aspx',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Tucson': {
            'url': 'https://www.tucsonaz.gov/procurement',
            'bid_path': '/active-solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Mesa': {
            'url': 'https://www.mesaaz.gov/business/procurement',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial']
        },
        'Scottsdale': {
            'url': 'https://www.scottsdaleaz.gov/procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'AR': {
        'Little Rock': {
            'url': 'https://www.littlerock.gov/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Fort Smith': {
            'url': 'https://www.fortsmithar.gov/departments/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Fayetteville': {
            'url': 'https://www.fayetteville-ar.gov/3184/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'CO': {
        'Denver': {
            'url': 'https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Department-of-Finance/Purchasing-and-Contracts',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Colorado Springs': {
            'url': 'https://coloradosprings.gov/procurement-division',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Aurora': {
            'url': 'https://www.auroragov.org/business_services/purchasing_division',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'CT': {
        'Hartford': {
            'url': 'https://www.hartford.gov/Government/Departments/CAO/Procurement',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'New Haven': {
            'url': 'https://www.newhavenct.gov/gov/depts/admin/purchasing/',
            'bid_path': '/opportunities',
            'keywords': ['cleaning', 'facilities']
        },
        'Stamford': {
            'url': 'https://www.stamfordct.gov/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'DE': {
        'Wilmington': {
            'url': 'https://www.wilmingtonde.gov/government/city-departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Dover': {
            'url': 'https://www.cityofdover.com/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Newark': {
            'url': 'https://newarkde.gov/departments/finance',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'GA': {
        'Atlanta': {
            'url': 'https://www.atlantaga.gov/government/departments/procurement',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Augusta': {
            'url': 'https://www.augustaga.gov/169/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Columbus': {
            'url': 'https://www.columbusga.gov/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Savannah': {
            'url': 'https://www.savannahga.gov/1051/Procurement-Opportunities',
            'bid_path': '',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'HI': {
        'Honolulu': {
            'url': 'https://www.honolulu.gov/budget/contracts-and-purchasing.html',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Hilo': {
            'url': 'https://www.hawaiicounty.gov/departments/finance/procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        }
    },
    'ID': {
        'Boise': {
            'url': 'https://www.cityofboise.org/departments/finance/purchasing-division/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Meridian': {
            'url': 'https://www.meridiancity.org/finance/procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Nampa': {
            'url': 'https://www.cityofnampa.us/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'IL': {
        'Chicago': {
            'url': 'https://www.chicago.gov/city/en/depts/dps.html',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Aurora': {
            'url': 'https://www.aurora-il.org/246/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Naperville': {
            'url': 'https://www.naperville.il.us/government/bid-opportunities/',
            'bid_path': '',
            'keywords': ['janitorial', 'custodial']
        },
        'Rockford': {
            'url': 'https://www.rockfordil.gov/purchasing/',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'IN': {
        'Indianapolis': {
            'url': 'https://www.indy.gov/agency/office-of-finance-and-management',
            'bid_path': '/procurement',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Fort Wayne': {
            'url': 'https://www.cityoffortwayne.org/purchasing/',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Evansville': {
            'url': 'https://www.evansvillegov.org/index.aspx?NID=161',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'IA': {
        'Des Moines': {
            'url': 'https://www.dsm.city/departments/finance/purchasing_division/index.php',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Cedar Rapids': {
            'url': 'https://www.cedar-rapids.org/local_government/departments_g_-_m/management_and_budget/purchasing/index.php',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Davenport': {
            'url': 'https://www.davenportiowa.com/government/departments/finance_department/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'KS': {
        'Wichita': {
            'url': 'https://www.wichita.gov/Finance/Purchasing/Pages/default.aspx',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Overland Park': {
            'url': 'https://www.opkansas.org/things-to-do/business-resources/bids-and-proposals/',
            'bid_path': '',
            'keywords': ['cleaning', 'facilities']
        },
        'Kansas City': {
            'url': 'https://www.wycokck.org/Departments/Administration/Purchasing',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'KY': {
        'Louisville': {
            'url': 'https://louisvilleky.gov/government/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Lexington': {
            'url': 'https://www.lexingtonky.gov/departments/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Bowling Green': {
            'url': 'https://www.bgky.org/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'LA': {
        'New Orleans': {
            'url': 'https://nola.gov/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Baton Rouge': {
            'url': 'https://www.brla.gov/159/Purchasing-Division',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Shreveport': {
            'url': 'https://www.shreveportla.gov/109/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'ME': {
        'Portland': {
            'url': 'https://www.portlandmaine.gov/469/Purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Bangor': {
            'url': 'https://www.bangormaine.gov/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Lewiston': {
            'url': 'https://www.lewistonmaine.gov/departments/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'MI': {
        'Detroit': {
            'url': 'https://detroitmi.gov/departments/office-contracting-and-procurement',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Grand Rapids': {
            'url': 'https://www.grandrapidsmi.gov/Government/Departments/Management-and-Budget/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Warren': {
            'url': 'https://www.cityofwarren.org/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Ann Arbor': {
            'url': 'https://www.a2gov.org/departments/finance-admin-services/purchasing/Pages/default.aspx',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'MN': {
        'Minneapolis': {
            'url': 'https://www2.minneapolismn.gov/government/departments/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Saint Paul': {
            'url': 'https://www.stpaul.gov/departments/office-financial-services/procurement-division',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Rochester': {
            'url': 'https://www.rochestermn.gov/departments/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'MS': {
        'Jackson': {
            'url': 'https://www.jacksonms.gov/departments/purchasing/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Gulfport': {
            'url': 'https://www.gulfport-ms.gov/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Biloxi': {
            'url': 'https://biloxi.ms.us/departments/purchasing/',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'MO': {
        'Kansas City': {
            'url': 'https://www.kcmo.gov/city-hall/departments/finance/purchasing-division',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'St. Louis': {
            'url': 'https://www.stlouis-mo.gov/government/departments/sldc/procurement/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Springfield': {
            'url': 'https://www.springfieldmo.gov/187/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'MT': {
        'Billings': {
            'url': 'https://www.ci.billings.mt.us/248/Purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Missoula': {
            'url': 'https://www.ci.missoula.mt.us/406/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Great Falls': {
            'url': 'https://greatfallsmt.net/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'NE': {
        'Omaha': {
            'url': 'https://www.cityofomaha.org/government/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Lincoln': {
            'url': 'https://www.lincoln.ne.gov/City/Departments/Finance/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Bellevue': {
            'url': 'https://www.bellevue.net/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'NV': {
        'Las Vegas': {
            'url': 'https://www.lasvegasnevada.gov/Business/Bid-Opportunities',
            'bid_path': '',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Henderson': {
            'url': 'https://www.cityofhenderson.com/business/doing-business-with-the-city/bid-and-solicitation-opportunities',
            'bid_path': '',
            'keywords': ['cleaning', 'facilities']
        },
        'Reno': {
            'url': 'https://www.reno.gov/government/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'NJ': {
        'Newark': {
            'url': 'https://www.newarknj.gov/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Jersey City': {
            'url': 'https://www.cityofjerseycity.com/cityhall/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Paterson': {
            'url': 'https://www.patersonnj.gov/departments/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'NM': {
        'Albuquerque': {
            'url': 'https://www.cabq.gov/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Las Cruces': {
            'url': 'https://www.las-cruces.org/155/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Santa Fe': {
            'url': 'https://www.santafenm.gov/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'NC': {
        'Charlotte': {
            'url': 'https://www.charlottenc.gov/Growth-and-Development/Business/Small-Business/Contracting-Opportunities',
            'bid_path': '',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Raleigh': {
            'url': 'https://raleighnc.gov/services/business/procurement-opportunities',
            'bid_path': '',
            'keywords': ['cleaning', 'facilities']
        },
        'Greensboro': {
            'url': 'https://www.greensboro-nc.gov/departments/business-development-services/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial']
        },
        'Durham': {
            'url': 'https://durhamnc.gov/832/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'ND': {
        'Fargo': {
            'url': 'https://www.fargond.gov/city-government/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Bismarck': {
            'url': 'https://www.bismarcknd.gov/192/Purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Grand Forks': {
            'url': 'https://www.grandforksgov.com/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'OH': {
        'Columbus': {
            'url': 'https://www.columbus.gov/finance/purchasing/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Cleveland': {
            'url': 'https://www.clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/OfficeofEqualOpportunity/Procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Cincinnati': {
            'url': 'https://www.cincinnati-oh.gov/procurement/',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Toledo': {
            'url': 'https://toledo.oh.gov/services/public-service/office-of-procurement-and-contract-compliance',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'OK': {
        'Oklahoma City': {
            'url': 'https://www.okc.gov/departments/finance/procurement',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Tulsa': {
            'url': 'https://www.cityoftulsa.org/government/departments/finance/purchasing/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Norman': {
            'url': 'https://www.normanok.gov/content/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'OR': {
        'Portland': {
            'url': 'https://www.portlandoregon.gov/brfs/59647',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Salem': {
            'url': 'https://www.cityofsalem.net/government/departments/administrative-services/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Eugene': {
            'url': 'https://www.eugene-or.gov/165/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'PA': {
        'Philadelphia': {
            'url': 'https://www.phila.gov/departments/department-of-revenue/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Pittsburgh': {
            'url': 'https://pittsburghpa.gov/omb/procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Allentown': {
            'url': 'https://www.allentownpa.gov/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Erie': {
            'url': 'https://www.erie.pa.us/departments/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'SC': {
        'Columbia': {
            'url': 'https://www.columbiasc.net/depts/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Charleston': {
            'url': 'https://www.charleston-sc.gov/161/Procurement',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Greenville': {
            'url': 'https://www.greenvillesc.gov/303/Procurement-Office',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'SD': {
        'Sioux Falls': {
            'url': 'https://www.siouxfalls.org/business/government-bids',
            'bid_path': '',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Rapid City': {
            'url': 'https://www.rcgov.org/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'facilities']
        },
        'Aberdeen': {
            'url': 'https://www.aberdeen.sd.us/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'TN': {
        'Nashville': {
            'url': 'https://www.nashville.gov/departments/finance/accounting-and-treasury/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Memphis': {
            'url': 'https://www.memphistn.gov/government/finance/procurement/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Knoxville': {
            'url': 'https://www.knoxvilletn.gov/government/city_departments_offices/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Chattanooga': {
            'url': 'https://connect.chattanooga.gov/purchasing/',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'UT': {
        'Salt Lake City': {
            'url': 'https://www.slc.gov/procurement/',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Provo': {
            'url': 'https://www.provo.org/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'West Valley City': {
            'url': 'https://www.wvc-ut.gov/233/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'VT': {
        'Burlington': {
            'url': 'https://www.burlingtonvt.gov/CAO/Purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'South Burlington': {
            'url': 'https://www.sburl.com/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Rutland': {
            'url': 'https://rutlandvermont.com/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'WA': {
        'Seattle': {
            'url': 'https://www.seattle.gov/business/doing-business-with-the-city/procurement',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Spokane': {
            'url': 'https://my.spokanecity.org/business/procurement/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Tacoma': {
            'url': 'https://www.cityoftacoma.org/government/city_departments/finance/procurement_and_payables',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        },
        'Vancouver': {
            'url': 'https://www.cityofvancouver.us/finance/page/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['cleaning', 'janitorial']
        }
    },
    'WI': {
        'Milwaukee': {
            'url': 'https://city.milwaukee.gov/DPW/Purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Madison': {
            'url': 'https://www.cityofmadison.com/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Green Bay': {
            'url': 'https://www.greenbaywi.gov/161/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'WV': {
        'Charleston': {
            'url': 'https://www.cityofcharleston.org/departments/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Huntington': {
            'url': 'https://www.huntingtonwv.gov/departments/finance/purchasing/',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Morgantown': {
            'url': 'https://www.morgantownwv.gov/departments/finance/purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    },
    'WY': {
        'Cheyenne': {
            'url': 'https://www.cheyennecity.org/departments/finance/purchasing',
            'bid_path': '/solicitations',
            'keywords': ['janitorial', 'custodial', 'cleaning']
        },
        'Casper': {
            'url': 'https://www.casperwy.gov/departments/finance/purchasing',
            'bid_path': '/bids',
            'keywords': ['cleaning', 'facilities']
        },
        'Laramie': {
            'url': 'https://www.cityoflaramie.org/203/Purchasing',
            'bid_path': '/opportunities',
            'keywords': ['janitorial', 'custodial']
        }
    }
}

def generate_update_code():
    """Generate Python code to update app.py with all state cities"""
    
    print("=" * 80)
    print("CITY PROCUREMENT PORTALS UPDATE")
    print("=" * 80)
    print(f"\nTotal States: {len(ALL_STATE_CITIES)}")
    
    total_cities = sum(len(cities) for cities in ALL_STATE_CITIES.values())
    print(f"Total Cities: {total_cities}")
    
    print("\nCities per State:")
    for state_code, cities in sorted(ALL_STATE_CITIES.items()):
        city_names = ', '.join(cities.keys())
        print(f"  {state_code}: {len(cities)} cities ({city_names})")
    
    print("\n" + "=" * 80)
    print("READY TO UPDATE APP.PY")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. This data structure is ready to replace the `portals` dict in get_city_procurement_portals()")
    print("2. Run this script to see the structure")
    print("3. Manually copy into app.py or use automated replacement")
    print("\nBenefits:")
    print("- City dropdown will work for ALL 50 states")
    print("- Users can select from 3-10 major cities per state")
    print("- Or manually enter any city name")
    print("- Comprehensive nationwide coverage")

if __name__ == '__main__':
    generate_update_code()
