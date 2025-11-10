# Nationwide Dynamic Pricing Calculator

## Overview
Enhanced pricing calculator that generates competitive bids based on **national averages, state-specific cost-of-living data, and local market conditions**. Helps contractors price services accurately across all 50 US states.

## Features Implemented ✅

### 1. Location-Based Pricing
- **50 US States**: Complete cost-of-living multiplier database (2024 data)
- **Metro Area Selection**: Rural (0.85x), Suburban (1.0x), Urban (1.15x), Major Metro (1.35x)
- **Auto-Calculated Labor Rates**: Based on national baseline ($16.50/hr) adjusted for location

### 2. State Cost Multipliers
**Lowest Cost States:**
- Mississippi: 0.84x
- Arkansas: 0.86x
- West Virginia: 0.86x
- Alabama: 0.87x

**Average Cost States:**
- Virginia: 1.03x
- Colorado: 1.05x
- Oregon: 1.07x

**Highest Cost States:**
- California: 1.38x
- New York: 1.39x
- District of Columbia: 1.52x
- Hawaii: 1.96x

### 3. Enhanced Facility Types
- Office Building (0.08/sq ft)
- Medical Facility (0.12/sq ft)
- School/Educational (0.07/sq ft)
- Government Building (0.09/sq ft)
- Industrial/Warehouse (0.06/sq ft)
- **NEW:** Retail Space (0.09/sq ft)
- **NEW:** Hotel/Hospitality (0.11/sq ft)
- **NEW:** Data Center (0.15/sq ft)

### 4. Market Competition Adjustments
- **High Competition**: Bid 7% lower to win contracts
- **Moderate Competition**: Standard market rate
- **Low Competition**: Bid 7% higher for better margins

### 5. Profit Margin Calculator
- Interactive slider (5-30%)
- Real-time calculation of profit amount
- Recommendations: 5-8% government, 8-12% competitive, 15-25% specialized

### 6. Additional Services (8 Options)
- Floor Care (stripping, waxing, buffing) - +15%
- Window Cleaning - +10%
- Carpet Cleaning - +12%
- **NEW:** Power Washing/Exterior - +8%
- Specialized/Medical-Grade Cleaning - +20%
- Green/Eco-Friendly Products - +10%
- **NEW:** After Hours/Weekend Service - +15%
- **NEW:** Supply Restocking & Management - +5%

### 7. Comprehensive Results Dashboard
- **Monthly Cost**: Total monthly service cost
- **Annual Cost**: 12-month contract value
- **Total Contract Value**: Multi-year contract total
- **Market Comparison Badge**: Shows if bid is below/at/above national average
- **Detailed Breakdown**:
  - Base cleaning services
  - State location adjustment
  - Metro area multiplier
  - Competition adjustment
  - Additional services (itemized)
  - Profit margin
  - **Per-sq-ft-per-month** metric
  - **Per-cleaning** cost metric

## How It Works

### Location-Based Calculation Flow
```
1. Select State (e.g., California)
   → Applies CA cost multiplier (1.38x)

2. Select Metro Area (e.g., Major Metro)
   → Applies metro multiplier (1.35x)

3. Labor Rate Auto-Calculated:
   National Base: $16.50/hr
   × State Multiplier: 1.38
   × Metro Multiplier: 1.35
   = Calculated Labor Rate: $30.76/hr

4. Base Rate Adjusted:
   National Base: $0.08/sq ft
   × State Multiplier: 1.38
   × Metro Multiplier: 1.35
   = Location-Adjusted Rate: $0.1490/sq ft

5. Apply Facility, Frequency, Service Level, Competition
6. Add Additional Services
7. Add Profit Margin
8. Compare to National Average
```

## Usage Examples

### Example 1: Virginia Suburban Office
- **State**: Virginia (1.03x)
- **Metro**: Suburban (1.0x)
- **Facility**: Office (0.08/sq ft)
- **Size**: 10,000 sq ft
- **Frequency**: 3x/week (12 cleanings/month)
- **Service Level**: Standard (1.0x)
- **Competition**: Moderate (1.0x)
- **Profit Margin**: 12%

**Labor Rate**: $16.50 × 1.03 × 1.0 = **$17.00/hr**
**Monthly Cost**: ~$10,296
**Market Comparison**: At National Average

### Example 2: New York Major Metro Medical
- **State**: New York (1.39x)
- **Metro**: Major Metro (1.35x)
- **Facility**: Medical (0.12/sq ft)
- **Size**: 15,000 sq ft
- **Frequency**: Daily (20 cleanings/month)
- **Service Level**: Premium (1.3x)
- **Additional**: Specialized Cleaning (+20%)
- **Competition**: High (0.93x)
- **Profit Margin**: 8%

**Labor Rate**: $16.50 × 1.39 × 1.35 = **$30.96/hr**
**Monthly Cost**: ~$52,883
**Market Comparison**: Above National Average (+45%)

### Example 3: Mississippi Rural School
- **State**: Mississippi (0.84x)
- **Metro**: Rural (0.85x)
- **Facility**: School (0.07/sq ft)
- **Size**: 50,000 sq ft
- **Frequency**: 2x/week (8 cleanings/month)
- **Service Level**: Basic (0.75x)
- **Competition**: Low (1.07x)
- **Profit Margin**: 15%

**Labor Rate**: $16.50 × 0.84 × 0.85 = **$11.78/hr**
**Monthly Cost**: ~$18,945
**Market Comparison**: Below National Average (-32%)

## Pricing Strategy Tips

### Government Contracts
- Use **5-8% profit margin** for competitive federal/state bids
- Check Davis-Bacon wage requirements (typically $5-10/hr higher)
- Select "High Competition" for GSA schedules
- Include all required services in additional options

### Commercial Contracts
- Use **12-18% profit margin** for private sector
- Adjust for metro area competition
- Bundle services (floor care + window cleaning) for better margins
- Offer multi-year discounts

### Economies of Scale
- **Under 10K sq ft**: Standard rates
- **10K-25K sq ft**: Consider -5% adjustment
- **25K-50K sq ft**: Consider -10% adjustment
- **50K+ sq ft**: Consider -15% adjustment
- Update base rate manually for large facilities

### Regional Considerations
- **High-cost states** (CA, NY, HI, DC): Expect 30-50% higher bids
- **Low-cost states** (MS, AR, WV, AL): Can bid 15-20% below national average
- **Major metros**: Labor shortages may justify +10-15% premium
- **Rural areas**: Factor in travel time/distance costs

## Access & Navigation

### Direct URL
`/pricing-calculator`

### Accessible From:
1. **Main Navigation** → Tools dropdown → "Pricing Calculator"
2. **Dashboard** → Quick Actions → "Pricing Calculator" button
3. **Resource Toolbox** → "Dynamic Pricing Tool" large button
4. **City Procurement** → Resources list → "Pricing Calculator"

## Technical Details

### Data Sources
- **State Cost-of-Living**: 2024 Missouri Economic Research and Information Center (MERIC)
- **Metro Area Multipliers**: Bureau of Labor Statistics (BLS) Metropolitan Statistical Areas
- **National Baseline**: $16.50/hr (2024 commercial cleaning industry average)
- **Facility Rates**: Industry standard per-square-foot rates (ISSA/BSCAI)

### Calculation Formula
```javascript
// Base calculation
baseRatePerSqft = facilityTypeRate × stateCostMultiplier × metroMultiplier

// Monthly base cost
baseMonthlyCost = sqft × baseRatePerSqft × serviceLevelMultiplier × frequencyMultiplier

// Competition adjustment
baseMonthlyCost × competitionMultiplier

// Additional services
additionalServicesCost = baseMonthlyCost × (sumOfServicePercentages / 100)

// Subtotal
subtotal = baseMonthlyCost + additionalServicesCost

// Final price
totalMonthlyCost = subtotal + (subtotal × profitMargin / 100)

// Market comparison
percentVsMarket = ((totalMonthlyCost - nationalAverage) / nationalAverage × 100)
```

### Auto-Calculation
- JavaScript recalculates on every input change
- Real-time updates to labor rate display
- Instant breakdown refresh
- No page reload required

## Benefits

### For Contractors
✅ **Accurate National Pricing**: Never over/under-bid again
✅ **State-Specific Rates**: Competitive in any market
✅ **Metro Area Adjustments**: Account for local labor costs
✅ **Market Comparison**: Know if your bid is competitive
✅ **Profit Margin Control**: Balance competitiveness vs profitability
✅ **Professional Estimates**: Detailed breakdowns for proposals

### For Business Development
✅ **Nationwide Expansion**: Bid confidently in any state
✅ **Competitive Intelligence**: Understand market positioning
✅ **Proposal Support**: Generate pricing for RFP responses
✅ **Multi-Location Pricing**: Standardized approach across regions
✅ **Data-Driven Decisions**: Based on real cost-of-living data

## Future Enhancements

### Planned Features
- [ ] **PDF Export**: Download professional proposal PDFs
- [ ] **Save Calculations**: Store estimates in customer dashboard
- [ ] **Email Quotes**: Send estimates to prospects
- [ ] **Historical Tracking**: Compare bids over time
- [ ] **Multi-Facility**: Bulk calculate for multiple sites
- [ ] **Custom Multipliers**: Override defaults for unique situations
- [ ] **Prevailing Wage Lookup**: Automatic Davis-Bacon rate integration
- [ ] **RFP Import**: Parse requirements from government RFPs
- [ ] **Competitor Analysis**: Benchmark against local market rates
- [ ] **Seasonal Adjustments**: Account for peak/off-peak pricing

## Commit Details
- **Commit**: `73bbc54`
- **Date**: November 5, 2025
- **Files Changed**: `templates/pricing_calculator.html`
- **Lines Added**: +233
- **Lines Removed**: -33

## Testing Checklist

✅ All 50 states selectable
✅ Metro area multipliers apply correctly
✅ Labor rate auto-calculates
✅ State multipliers affect pricing (verified MS vs NY)
✅ Competition adjustments work (high/moderate/low)
✅ Profit margin slider updates in real-time
✅ All 8 additional services calculate correctly
✅ Market comparison badge displays (below/at/above)
✅ Per-sq-ft and per-cleaning metrics accurate
✅ Breakdown table shows all adjustments
✅ Page loads without errors
✅ Responsive on mobile devices

## Support
For questions about pricing methodology, state multipliers, or calculation accuracy, refer to the detailed breakdown table and pricing strategy tips section of the calculator. All calculations are based on 2024 industry data and are automatically updated.
