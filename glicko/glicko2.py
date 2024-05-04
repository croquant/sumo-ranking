"""
Copyright (c) 2009 Ryan Kirkman

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import math

from .constants import (
    CONVERGENCE_TOLERANCE,
    DEFAULT_RATING,
    DEFAULT_RD,
    DEFAULT_VOLATILITY,
    GLICKO2_SCALER,
    TAU,
)


class Player:
    def get_rating(self):
        return (self.__rating * GLICKO2_SCALER) + DEFAULT_RATING

    def set_rating(self, rating):
        self.__rating = (rating - DEFAULT_RATING) / GLICKO2_SCALER

    rating = property(get_rating, set_rating)

    def get_rd(self):
        return self.__rd * GLICKO2_SCALER

    def set_rd(self, rd):
        self.__rd = rd / GLICKO2_SCALER

    rd = property(get_rd, set_rd)

    def __init__(
        self,
        rating=DEFAULT_RATING,
        rd=DEFAULT_RD,
        vol=DEFAULT_VOLATILITY,
        tau=TAU,
    ):
        # For testing purposes, preload the values
        # assigned to an unrated player.
        self._tau = tau
        self.set_rating(rating)
        self.set_rd(rd)
        self.vol = vol

    def _pre_rating_rd(self):
        """Calculates and updates the player's rating deviation for the
        beginning of a rating period.

        preRatingRD() -> None

        """
        self.__rd = math.sqrt(math.pow(self.__rd, 2) + math.pow(self.vol, 2))

    def update_player(self, rating_list, rd_list, outcome_list):
        """Calculates the new rating and rating deviation of the player.

        update_player(list[int], list[int], list[bool]) -> None

        """
        # Convert the rating and rating deviation values for internal use.
        rating_list = [
            (x - DEFAULT_RATING) / GLICKO2_SCALER for x in rating_list
        ]
        rd_list = [x / GLICKO2_SCALER for x in rd_list]

        v = self._v(rating_list, rd_list)
        self.vol = self._new_vol(rating_list, rd_list, outcome_list, v)
        self._pre_rating_rd()

        self.__rd = 1 / math.sqrt((1 / math.pow(self.__rd, 2)) + (1 / v))

        temp_sum = 0
        for i in range(len(rating_list)):
            temp_sum += self._g(rd_list[i]) * (
                outcome_list[i] - self._e(rating_list[i], rd_list[i])
            )
        self.__rating += math.pow(self.__rd, 2) * temp_sum

    # step 5
    def _new_vol(self, rating_list, rd_list, outcome_list, v):
        """Calculating the new volatility as per the Glicko2 system.

        Updated for Feb 22, 2012 revision. -Leo

        _newVol(list, list, list, float) -> float

        """
        # step 1
        a = math.log(self.vol**2)
        eps = CONVERGENCE_TOLERANCE
        _a = a

        # step 2
        b = None
        delta = self._delta(rating_list, rd_list, outcome_list, v)
        tau = self._tau
        if (delta**2) > ((self.__rd**2) + v):
            b = math.log(delta**2 - self.__rd**2 - v)
        else:
            k = 1
            while self._f(a - k * math.sqrt(tau**2), delta, v, a) < 0:
                k = k + 1
            b = a - k * math.sqrt(tau**2)

        # step 3
        f_a = self._f(_a, delta, v, a)
        f_b = self._f(b, delta, v, a)

        # step 4
        while math.fabs(b - _a) > eps:
            # a
            c = _a + ((_a - b) * f_a) / (f_b - f_a)
            f_c = self._f(c, delta, v, a)
            # b
            if f_c * f_b <= 0:
                _a = b
                f_a = f_b
            else:
                f_a = f_a / 2.0
            # c
            b = c
            f_b = f_c

        # step 5
        return math.exp(_a / 2)

    def _f(self, x, delta, v, a):
        ex = math.exp(x)
        num1 = ex * (delta**2 - self.__rating**2 - v - ex)
        denom1 = 2 * ((self.__rating**2 + v + ex) ** 2)
        return (num1 / denom1) - ((x - a) / (self._tau**2))

    def _delta(self, rating_list, rd_list, outcome_list, v):
        """The delta function of the Glicko2 system.

        _delta(list, list, list) -> float

        """
        temp_sum = 0
        for i in range(len(rating_list)):
            temp_sum += self._g(rd_list[i]) * (
                outcome_list[i] - self._e(rating_list[i], rd_list[i])
            )
        return v * temp_sum

    def _v(self, rating_list, rd_list):
        """The v function of the Glicko2 system.

        _v(list[int], list[int]) -> float

        """
        temp_sum = 0
        for i in range(len(rating_list)):
            temp_e = self._e(rating_list[i], rd_list[i])
            temp_sum += (
                math.pow(self._g(rd_list[i]), 2) * temp_e * (1 - temp_e)
            )
        return 1 / max(temp_sum, 0.00001)

    def _e(self, p2rating, p2rd):
        """The Glicko E function.

        _E(int) -> float

        """
        return 1 / (
            1 + math.exp(-1 * self._g(p2rd) * (self.__rating - p2rating))
        )

    def _g(self, rd):
        """The Glicko2 g(RD) function.

        _g() -> float

        """
        return 1 / math.sqrt(1 + 3 * math.pow(rd, 2) / math.pow(math.pi, 2))

    def did_not_compete(self):
        """Applies Step 6 of the algorithm. Use this for
        players who did not compete in the rating period.

        did_not_compete() -> None

        """
        self._pre_rating_rd()
