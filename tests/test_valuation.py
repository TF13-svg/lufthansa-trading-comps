from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from valuation import implied_price,load_data,ranges

class ValuationTests(unittest.TestCase):
 def test_net_cash_increases_equity(self):
  self.assertAlmostEqual(implied_price(4,100,-20,10),42)
 def test_invalid_denominator_is_rejected(self):
  with self.assertRaises(ValueError):implied_price(4,100,20,0)
 def test_iag_treasury_deduction(self):
  df,_,_=load_data();r=df[df.company=='IAG'].iloc[0]
  self.assertAlmostEqual(r.shares_m,4611.669527-241.649536)
 def test_easyjet_currency_invariance(self):
  df,_,_=load_data();r=df[df.company=='easyJet'].iloc[0]
  local_price=r.close/100
  self.assertAlmostEqual(r.EV_EBITDA,(local_price*r.shares_m+r.net_debt)/r.EBITDA)
 def test_target_is_not_in_peer_set(self):
  df,_,_=load_data();r=ranges(df)
  self.assertEqual(list(r.n),[2,2,5,5,3,3])
 def test_wizz_disclosure_difference_is_retained(self):
  df,b,_=load_data();self.assertAlmostEqual(df[df.company=='Wizz Air'].iloc[0].EBITDA,1164.2)
  self.assertAlmostEqual(b[(b.company=='Wizz Air')&(b.metric=='EBITDA')].iloc[0].calculated_ltm,1165.5)

if __name__=='__main__':unittest.main()
