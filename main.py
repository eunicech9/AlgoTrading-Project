'''
    BOLLINGER BAND AND RSI TRADING STRATEGY
    ------------------------  
    This is a basic mean reversion trading strategy 
    using Bollinger Bands and RSI as indicators.
    
    Strategy built in Quantconnect.com
    -
    Created by Eunice
    https://github.com/eunicech9
    -
'''
class BollingerBandandRSI(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)  # Set Start Date
        # self.SetStartDate(2019, 1, 1)  # Set Start Date
        # self.SetEndDate(2020, 12, 31)  # Set End Date
        self.SetCash(100000)  # Set Strategy Cash

        self.long_list = ["Long"]
        self.short_list = ["Short"]
        
        self.stop = False
        
        # Dictionaries to store values
        self.stocktickers = ["BCRX", "C", "BA", "SHOP", "M"]

        self.rsi = {}
        self.bband = {}
        
        self.signal = {}
        self.stop_loss_high = {}
        self.stop_loss_low = {}
        
        for stock in self.stocktickers:
            self.AddEquity(stock, Resolution.Daily)
            
            # create a RSI
            self.rsi[stock] = self.RSI(stock, 14)
            
            # create a bollinger band
            self.bband[stock] = self.BB(stock, 30, 2, MovingAverageType.Simple, Resolution.Daily)
    
            self.signal[stock] = None
            self.stop_loss_high[stock] = None
            self.stop_loss_low[stock] = None
            
            # set warmup period
            self.SetWarmUp(31)
        

    def OnData(self, data):

        if self.stop:
            self.Debug("self stop")
            return
        
        for stock in self.stocktickers:
            
            stock_data = self.History([stock], 30, Resolution.Daily)
            prev_high = max(stock_data.high)
            prev_low = min(stock_data.low)
            prev_close = stock_data.close[-1]
            prev_close_2 = stock_data.close[-2]
            current = self.Securities[stock].Price
            
            
            if not self.rsi[stock].IsReady and not self.bband[stock].IsReady:
                return
            
            
            if stock not in self.long_list and stock not in self.short_list:
                
                # 1. Register Long or Short signals            
                
                # [LONG] If (i) RSI < 25, (ii) price closes below lower bollinger band and (iii) current price above price close then BUY signal
                if self.rsi[stock].Current.Value < 25 \
                and prev_close_2 < self.bband[stock].LowerBand.Current.Value \
                and current >= prev_close:
                    self.signal[stock] = "Long"
                    self.Debug("Long signal: {}".format(stock))

                # [SHORT] If (i) RSI > 75, (ii) price closes above upper bollinger band and (iii) current price below price close then SELL signal
                if self.rsi[stock].Current.Value > 75 \
                and prev_close_2 > self.bband[stock].UpperBand.Current.Value \
                and current <= prev_close:
                    self.signal[stock] = "Short"
                    self.Debug("Short signal: {}".format(stock))

                # 2. First Trade Entry            

                # [LONG] If signal is Long and current price re-enter lower band then LONG stock
                if self.signal[stock] == "Long" \
                and current > self.bband[stock].LowerBand.Current.Value:
                    self.SetHoldings(stock, 0.15)
                    self.stop_loss_low[stock] = prev_low
                    self.long_list.append(stock)
                    self.signal[stock] = None

                # [SHORT] If signal is Short and current price re-enter upper band then SHORT stock
                if self.signal[stock] == "Short" \
                and current < self.bband[stock].UpperBand.Current.Value:
                    self.SetHoldings(stock, -0.15)
                    self.stop_loss_high[stock] = prev_high
                    self.short_list.append(stock)
                    self.signal[stock] = None

            # 3. Exit conditions, only if we are invested
            if stock in self.long_list and self.Securities[stock].Invested:
                
                # Stop loss at prev_low  
                if current <= self.stop_loss_low[stock]:
                    self.Liquidate(stock, "stop-loss")
                    self.long_list.remove(stock)
                    
                # Take profit when reverts to middle band    
                elif current >= self.bband[stock].MiddleBand.Current.Value:
                    self.Liquidate(stock, "take-profit")
                    self.long_list.remove(stock)
                    
        
            if stock in self.short_list and self.Securities[stock].Invested:       
                self.Debug("stock: {}, prev_high: {}, prev_low: {}, current: {}".format(stock, prev_high, prev_low, current))
                
                # Stop loss at prev_high  
                if current >= self.stop_loss_high[stock]:
                    self.Liquidate(stock, "stop-loss")
                    self.short_list.remove(stock)
                    
                # Take profit when reverts to middle band
                elif current <= self.bband[stock].MiddleBand.Current.Value:
                    self.Liquidate(stock, "take-profit")
                    self.short_list.remove(stock)
                    
                    
        if (self.Portfolio.Cash + self.Portfolio.UnsettledCash) < 80000:
            self.stop = True
            self.Liquidate()
        
  