from decimal import Decimal


class BullishCandleSticks:
    def __init__(self, historical_data):
        self.historical_data = historical_data

    def hammer(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Hammer pattern: small body at the top, long lower shadow
            if (curr_close - curr_open) / (curr_high - curr_low) < 0.3 and \
               (curr_high - max(curr_open, curr_close)) / (curr_high - curr_low) > 0.5:
                return True
        return False
    
    def morning_star(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Morning star pattern: bearish candle, small body, bullish candle
            if (prev_close < prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close > next_open):
                return True
        return False
    
    def three_white_soldiers(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Three white soldiers pattern: three consecutive bullish candles
            if (prev_close > prev_open and curr_close > curr_open and \
                next_close > next_open):
                return True
        return False
    
    def bullish_engulfing(self):
        # Assumes data is a list of dicts with 'open', 'close', 'high', 'low'
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])

            # Previous candle bearish, current candle bullish and engulfs previous
            if prev_close < prev_open and curr_close > curr_open:
                if curr_close > prev_open and curr_open < prev_close:
                    return True
        return False
    
    def bullish_three_line_strike(self):
        for i in range(3, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Bullish three line strike pattern: three consecutive bullish candles followed by a bearish candle
            if (prev_close > prev_open and curr_close > curr_open and \
                next_close < next_open):
                return True
        return False
    
    def three_inside_up(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Three inside up pattern: two small bodies within a larger body
            if (prev_close < prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close > next_open):
                return True
        return False
    
    def dragonfly_doji(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Dragonfly doji pattern: small body at the top, long lower shadow
            if (curr_close - curr_open) / (curr_high - curr_low) < 0.3 and \
               (curr_high - max(curr_open, curr_close)) / (curr_high - curr_low) > 0.5:
                return True
        return False

    def piercing_line(self):
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])

            # Piercing line pattern: bullish candle opens below previous bearish candle's low and closes above its midpoint
            if (curr_open < prev_close and curr_close > (prev_open + prev_close) / 2):
                return True
        return False
    
    def bullish_marubozu(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Bullish marubozu pattern: no shadows, long body
            if (curr_open == curr_close and \
                (curr_high - curr_open) / (curr_high - curr_low) > 0.8):
                return True
        return False
    
    def bullish_abandoned_baby(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Bullish abandoned baby pattern: bearish candle, doji, bullish candle
            if (prev_close < prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close > next_open):
                return True
        return False
    
    def rising_window(self):
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            

            # Rising window pattern: gap up between two candles
            if (curr_open > prev_close and curr_close > curr_open):
                return True
        return False


class BearishCandleSticks:
    def __init__(self, historical_data):
        self.historical_data = historical_data

    def evening_star(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Evening star pattern: bullish candle, small body, bearish candle
            if (prev_close > prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close < next_open):
                return True
        return False
    
    def three_black_crows(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Three black crows pattern: three consecutive bearish candles
            if (prev_close < prev_open and curr_close < curr_open and \
                next_close < next_open):
                return True
        return False
    
    def hanging_man(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # hanging man pattern: small body at the bottom, long upper shadow
            if (curr_close - curr_open) / (curr_high - curr_low) < 0.3 and \
               (curr_high - min(curr_open, curr_close)) / (curr_high - curr_low) > 0.5:
                return True
        return False
    
    def shooting_star(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Shooting star pattern: small body at the bottom, long upper shadow
            if (curr_close - curr_open) / (curr_high - curr_low) < 0.3 and \
               (curr_high - min(curr_open, curr_close)) / (curr_high - curr_low) > 0.5:
                return True
        return False
    
    def bearish_engulfing(self):
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])

            if prev_close > prev_open and curr_close < curr_open:
                if curr_open > prev_close and curr_close < prev_open:
                    return True
        return False
    
    def bearish_three_line_strike(self):
        for i in range(3, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Bearish three line strike pattern: three consecutive bearish candles followed by a bullish candle
            if (prev_close < prev_open and curr_close < curr_open and \
                next_close > next_open):
                return True
        return False

    def three_inside_down(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Three inside down pattern: two small bodies within a larger body
            if (prev_close > prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close < next_open):
                return True
        return False
    
    def gravestone_doji(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Gravestone doji pattern: small body at the bottom, long upper shadow
            if (curr_close - curr_open) / (curr_high - curr_low) < 0.3 and \
               (curr_high - min(curr_open, curr_close)) / (curr_high - curr_low) > 0.5:
                return True
        return False
    
    def dark_cloud_cover(self):
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])

            # Dark cloud cover pattern: bearish candle opens above previous bullish candle's high and closes below its midpoint
            if (curr_open > prev_close and curr_close < (prev_open + prev_close) / 2):
                return True
        return False
    
    def bearish_marubozu(self):
        for i in range(1, len(self.historical_data)):
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            curr_high = Decimal(curr["high"])
            curr_low = Decimal(curr["low"])

            # Bearish marubozu pattern: no shadows, long body
            if (curr_open == curr_close and \
                (curr_high - curr_open) / (curr_high - curr_low) > 0.8):
                return True
        return False
    
    def bearish_abandoned_baby(self):
        for i in range(2, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]
            next_candle = self.historical_data[(len(self.historical_data)-i)-2]

            prev_open = Decimal(prev["open"])
            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])
            next_open = Decimal(next_candle["open"])
            next_close = Decimal(next_candle["close"])

            # Bearish abandoned baby pattern: bullish candle, doji, bearish candle
            if (prev_close > prev_open and abs(curr_close - curr_open) < 0.1 * abs(prev_close - prev_open) and \
                next_close < next_open):
                return True
        return False
    
    def falling_window(self):
        for i in range(1, len(self.historical_data)):
            prev = self.historical_data[len(self.historical_data)-i]
            curr = self.historical_data[(len(self.historical_data)-i)-1]

            prev_close = Decimal(prev["close"])
            curr_open = Decimal(curr["open"])
            curr_close = Decimal(curr["close"])

            # Falling window pattern: gap down between two candles
            if (curr_open < prev_close and curr_close < curr_open):
                return True
        return False
