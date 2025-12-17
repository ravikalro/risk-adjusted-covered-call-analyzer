# Changes Summary - Risk-Adjusted Covered Call Analyzer

## Latest Update: Unified Analysis & Export Logic

### 🎯 Key Changes

#### 1. **Simplified Configuration**
- **Before**: Min DTE (14 days) + Max DTE (41 days) = 2 parameters
- **After**: Number of Weeks (6) = 1 parameter
- **Why**: More intuitive - "analyze the next 6 weekly expirations"

#### 2. **Unified Delta Filter**
- **Before**: 
  - Main analysis: Delta ≤ Max_Delta (0.31)
  - CSV export: Delta between 0.20-0.32 (fixed)
- **After**: Both use Delta ≤ Max_Delta (0.31, configurable)

#### 3. **Unified Expiry Selection**
- **Before**:
  - Main analysis: All expiries within DTE range (14-41 days)
  - CSV export: First 6 chronological expiries
- **After**: Both use first N weekly expirations (where N = Number of Weeks)

#### 4. **Unified Sorting**
- **Before**: CSV export was unsorted (chronological)
- **After**: CSV export uses same sorting as main display (Stability Score → IV)

---

## Algorithm Flow (Both Analysis & Export)

```
1. Select Next N Weeks
   └─ Take first N expirations chronologically

2. Filter Options
   ├─ Delta ≤ Max_Delta (default: 0.31)
   └─ Strike > Spot Price (OTM only)

3. Group by Expiry Date
   └─ Select option with MAX PREMIUM per date

4. Calculate Metrics
   ├─ ARIF = (Premium × 365 × 100) / (Stock_Price × DTE)
   └─ Stability Score = |Theta| / Gamma

5. Rank & Sort
   ├─ Primary: Stability Score (DESC)
   └─ Tie-breaker: IV (DESC)

6. Display/Export
   └─ All ranked candidates
```

---

## What's Displayed

### Main Analysis Table
- All candidates (one per expiry)
- Ranked by Stability Score
- Shows: Expiration, DTE, Strike, Premium, Delta, Gamma, Theta, IV, Stability Score, ARIF, Volume, OI

### CSV Export
- **Identical data** to main analysis table
- Same filters, same sorting
- Additional columns: Bid, Ask, Break Even, Vega, Rho, Intrinsic Value

---

## Benefits of These Changes

✅ **Consistency**: Analysis and export now show identical results
✅ **Simplicity**: One "Number of Weeks" parameter instead of two DTE parameters
✅ **Clarity**: Export is sorted by quality (Stability Score) not just chronologically
✅ **Flexibility**: Easy to change time horizon (1-12 weeks)
