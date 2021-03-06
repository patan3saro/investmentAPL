import numpy as np

import business_logic.coop_properties as cp
from business_logic import core
from scipy.optimize import linprog
import business_logic.constant as const


class Game:
    def __init__(self, investors_number, price_cpu, hosting_capacity, duration_cpu):
        self.c_vec = None
        self.coalition = None
        self.p_cpu = price_cpu
        self.duration_cpu = duration_cpu
        self.hosting_capacity = hosting_capacity
        self.investors_number = investors_number

    # this function convert the load from requests per timeslot
    # to millicore (computational resources needed to serve the load)

    def calculate_coal_payoff(self):
        # matrix with all the b for each player
        b = np.zeros(shape=self.investors_number * const.T_HORIZON)
        c = np.zeros(shape=2 * self.investors_number * const.T_HORIZON + self.investors_number + 1)
        # if the network operator is not in the coalition or It is alone etc..
        check_NO = next((x for x in self.coalition if x.type == 'NO'), True)
        # print((check_NO,) == self.coalition, (check_NO,), self.coalition)
        # I write the comparison == with true because if no I return the object in some case
        condition = check_NO == True or (check_NO,) == self.coalition or (len(self.coalition) == 0) or (
                len(self.coalition) == 1)
        # print("condition", condition)

        if not condition:
            # we calculate utility function for all t for a player only for SPs
            # coalition is a tuple of investors
            b = np.array([])
            c = np.array([])

            for i in range(self.investors_number):
                # if there is that investor in the coalition we create the array for that player
                check = next((x for x in self.coalition if x.index == i), False)
                if check != False:
                    tmp0 = check.converted_load_all_t()
                    tmp1 = check.beta * np.ones(shape=const.T_HORIZON)
                else:
                    tmp0 = np.zeros(shape=const.T_HORIZON)
                    tmp1 = tmp0

                b = np.concatenate((b, tmp0))
                c = np.concatenate((c, tmp1))

            # Creating c vector
            # cost vector with benefit factor and cpu price
            c = np.concatenate((c, np.zeros(shape=self.investors_number),
                                const.CHI * np.ones(shape=self.investors_number * const.T_HORIZON), [-self.p_cpu]))
            # store c to use it later
            self.c_vec = c
        # Creating A matrix
        identity = np.identity(self.investors_number * const.T_HORIZON)
        zeros = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number * const.T_HORIZON))
        zeros_column = np.zeros(shape=(self.investors_number * const.T_HORIZON, 1))
        tmp0 = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number))
        mega_row_A0 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        tmp = 0
        for col in range(self.investors_number):
            for row in range(const.T_HORIZON):
                tmp0[row + tmp, col] = -1
            tmp += const.T_HORIZON

        mega_row_A1 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        mega_row_A2 = np.concatenate((zeros, identity, tmp0, zeros_column), axis=1)

        tmp = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number))
        mega_row_A3 = np.concatenate((zeros, identity, -tmp, zeros_column), axis=1)

        tmp0 = np.zeros(shape=(1, 2 * self.investors_number * const.T_HORIZON))
        tmp1 = np.zeros(shape=(1, self.investors_number))
        mega_row_A4 = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)

        tmp1 = np.ones(shape=(1, self.investors_number))
        A_eq = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)
        b_eq = [[0]]

        A = np.concatenate((mega_row_A0, mega_row_A1, mega_row_A2, mega_row_A3, mega_row_A4), axis=0)

        tmp0 = np.zeros(shape=(self.investors_number * const.T_HORIZON))
        b = np.concatenate((b, tmp0, b, tmp0, [self.hosting_capacity]), axis=0)
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (4 * self.investors_number * const.T_HORIZON + self.investors_number + 1)
        params = (c, A, b, A_eq, b_eq, bounds, const.T_HORIZON)
        sol = core.find_core(params)
        return sol

    def calculate_payoffs(self, infos_all_coal_one_config, players_number, coalitions):

        # getting the value of the grand coalition
        grand_coal_payoff = infos_all_coal_one_config[-1]["coalitional_payoff"]
        length = players_number
        unfair_payoff = [] * length
        tmp = grand_coal_payoff
        # to share in unfair way the revenues
        for i in range(length):
            tmp /= 2
            unfair_payoff.append(tmp)
        msg = "The Unfair payoff is:"
        return unfair_payoff, msg

    def set_coalition(self, coalition):
        self.coalition = coalition

    def verify_properties(self, all_coal_payoff, coal_payoff, payoffs_vector):
        print("Verifying properties of payoffs \n")
        if cp.is_an_imputation(coal_payoff, payoffs_vector):
            print("The vector is an imputation (efficiency + individual rationality)!\n")
            print("Check if payoff vector is group rational...\n")
            if cp.is_group_rational(all_coal_payoff, -coal_payoff):
                print("The payoff vector is group rational!\n")
                print("The payoff vector is in the core!\n")
                print("Core verification terminated SUCCESSFULLY!\n")
                return True
            else:
                print("The payoff vector isn't group rational!\n")
                print("The payoff vector is not in the core!\n")
                print("Core verification terminated unsuccessfully!\n")
        else:
            print("The payoff vector isn't an imputation\n")
            print("Core verification terminated unsuccessfully!\n")
        return False

    def split_rev_paym(self, payoff_vector, resrc_split_vec):
        # recovering c vector
        c = self.c_vec
        # building A matrix
        identity = np.identity(self.investors_number)
        tmp0 = np.concatenate((identity, -identity), axis=1)
        ones = np.ones(shape=(1, self.investors_number))
        zeros = np.zeros(shape=(1, self.investors_number))
        tmp1 = np.concatenate((ones, zeros), axis=1)
        zeros = np.zeros(shape=(self.investors_number - 1, self.investors_number + 1))
        identity = np.identity(self.investors_number - 1)
        tmp2 = np.concatenate((identity, zeros), axis=1)
        A_eq = np.concatenate((tmp0, tmp1, tmp2), axis=0)
        # building b vector
        b_eq = np.zeros(shape=(self.investors_number + 1))
        tmp0 = (np.array(payoff_vector[:-1]) / (sum(payoff_vector) + 0.000001)) * (sum(payoff_vector) +
                                                                                   self.p_cpu * resrc_split_vec[-1])

        for i in range(self.investors_number):
            b_eq[i] = payoff_vector[i]

        b_eq[-1] = np.matmul(resrc_split_vec[:len(c)], c)
        coefficients_min_y = [0] * (len(A_eq[0]))
        b_eq = np.concatenate((np.array(b_eq), tmp0), axis=0)
        res = linprog(coefficients_min_y, A_eq=A_eq, b_eq=b_eq, method="simplex")
        return res['x'][0:self.investors_number], res['x'][self.investors_number:]
