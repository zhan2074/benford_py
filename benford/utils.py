from pandas import Series, DataFrame
from numpy import array, arange, log10
from .expected import First, Second, LastTwo
from .constants import digs_dict


def _set_N_(len_df, limit_N):
    # Assigning to N the superior limit or the lenght of the series
    if limit_N is None or limit_N > len_df:
        return len_df
    # Check on limit_N being a positive integer
    else:
        if limit_N < 0 or not isinstance(limit_N, int):
            raise ValueError("limit_N must be None or a positive integer.")
        else:
            return limit_N


def _test_(digs):
    '''
    Returns the base instance for the proper test to be performed
    depending on the digit
    '''
    if digs in [1, 2, 3]:
        return First(digs, plot=False)
    elif digs == 22:
        return Second(plot=False)
    else:
        return LastTwo(num=True, plot=False)


def _lt_(num=False):
    '''
    Creates an array with the possible last two digits

    Parameters
    ----------

    num: returns numeric (ints) values. Defaluts to False,
        which returns strings.
    '''
    if num:
        n = arange(0, 100)
    else:
        n = arange(0, 100).astype(str)
        n[:10] = array(['00', '01', '02', '03', '04', '05',
                           '06', '07', '08', '09'])
    return n


def _getMantissas_(arr):
    '''
    Returns the  mantissas, the non-integer part of the log of a number.

    arr: array of integers or floats ---> array of floats
    '''
    log_a = abs(log10(arr))
    return log_a - log_a.astype(int)  # the number - its integer part


def _input_data_(given):
    '''
    '''
    if (type(given) == Series) | (type(given) == ndarray):
        data = chosen = given
    elif type(given) == tuple:
        if (type(given[0]) != DataFrame) | (type(given[1]) != str):
            raise TypeError('The data tuple must be composed of a pandas '
                            'DataFrame and the name (str) of the chosen '
                            'column, in that order')
        data = given[0]
        chosen = given[0][given[1]]
    else:
        raise TypeError("Wrong data input type. Check docstring.")
    return data, chosen


def _prep_(data, digs, limit_N, simple=False, confidence=None):
    '''
    Transforms the original number sequence into a DataFrame reduced
    by the ocurrences of the chosen digits, creating other computed
    columns
    '''
    N = _set_N_(len(data), limit_N=limit_N)

    # get the number of occurrences of the digits
    v = data.value_counts()
    # get their relative frequencies
    p = data.value_counts(normalize=True)
    # crate dataframe from them
    dd = DataFrame({'Counts': v, 'Found': p}).sort_index()
    # join the dataframe with the one of expected Benford's frequencies
    dd = _test_(digs).join(dd).fillna(0)
    # create column with absolute differences
    dd['Dif'] = dd.Found - dd.Expected
    dd['AbsDif'] = dd.Dif.abs()
    if simple:
        del dd['Dif']
        return dd
    else:
        if confidence is not None:
            dd['Z_score'] = _Z_score(dd, N)
        return N, dd

def _check_digs_(digs):
    '''
    Chhecks the possible values for the digs of the First Digits test1
    '''
    if digs not in [1, 2, 3]:
        raise ValueError("The value assigned to the parameter -digs- "
                         f"was {digs}. Value must be 1, 2 or 3.")


def _check_test_(test):
    '''
    Checks the test chosen, both for int or str values
    '''
    if isinstance(test, int):
        if test in digs_dict.keys():
            return test
        else:
            raise ValueError(f'Test was set to {test}. Should be one of '
                             f'{digs_dict.keys()}')
    elif isinstance(test, str):
        if test in rev_digs.keys():
            return rev_digs[test]
        else:
            raise ValueError(f'Test was set to {test}. Should be one of '
                             f'{rev_digs.keys()}')
    else:
        raise ValueError('Wrong value chosen for test parameter. Possible '
                         f'values are\n {list(digs_dict.keys())} for ints and'
                         f'\n {list(rev_digs.keys())} for strings.')

def _check_confidence_(confidence):
    '''
    '''
    if confidence not in confs.keys():
        raise ValueError("Value of parameter -confidence- must be one of the "
                         f"following:\n {list(confs.keys())}")
    return confidence

def _check_high_Z_(high_Z):
    '''
    '''
    if not high_Z in ['pos', 'all']:
        if not isinstance(high_Z, int):
            raise ValueError("The parameter -high_Z- should be 'pos', "
                             "'all' or an int.")
    return high_Z

def _check_num_array(data):
    '''
    '''
    if (not isinstance(data, array)) & (not isinstance(data, Series)):
        print('\n`data` not a numpy NDarray nor a pandas Series.'
                ' Trying to convert...')
        try:
            data = array(data)
        except:
            raise ValueError('Could not convert data. Check input.')
        print('\nConversion successful.')
    elif (data.dtype == int) | (not data.dtype == float):
        print("\n`data` type not int nor float. Trying to convert...")
        try:
            data = data.astype(float)
        except:
            raise ValueError('Could not convert data. Check input.')
    return data


def _subtract_sorted_(data):
    '''
    Subtracts the sorted sequence elements from each other, discarding zeros.
    Used in the Second Order test
    '''
    sec = data.copy()
    sec.sort_values(inplace=True)
    sec = sec - sec.shift(1)
    sec = sec.loc[sec != 0]
    return sec

def _prep_to_roll_(start, test):
    '''
    Used by the rolling mad and rolling mean, prepares each test and
    respective expected proportions for later application to the Series subset
    '''
    if test in [1, 2, 3]:
        start[digs_dict[test]] = start.ZN // 10 ** ((
            log10(start.ZN).astype(int)) - (test - 1))
        start = start.loc[start.ZN >= 10 ** (test - 1)]

        ind = arange(10 ** (test - 1), 10 ** test)
        Exp = log10(1 + (1. / ind))

    elif test == 22:
        start[digs_dict[test]] = (start.ZN // 10 ** ((
            log10(start.ZN)).astype(int) - 1)) % 10
        start = start.loc[start.ZN >= 10]

        Expec = log10(1 + (1. / arange(10, 100)))
        temp = DataFrame({'Expected': Expec, 'Sec_Dig':
                             array(list(range(10)) * 9)})
        Exp = temp.groupby('Sec_Dig').sum().values.reshape(10,)
        ind = arange(0, 10)

    else:
        start[digs_dict[test]] = start.ZN % 100
        start = start.loc[start.ZN >= 1000]

        ind = arange(0, 100)
        Exp = array([1 / 99.] * 100)

    return Exp, ind

def _mad_to_roll_(arr, Exp, ind):
    '''
    Mean Absolute Deviation used in the rolling function
    '''
    prop = Series(arr)
    prop = prop.value_counts(normalize=True).sort_index()

    if len(prop) < len(Exp):
        prop = prop.reindex(ind).fillna(0)

    return abs(prop - Exp).mean()

def _mse_to_roll_(arr, Exp, ind):
    '''
    Mean Squared Error used in the rolling function
    '''
    prop = Series(arr)
    temp = prop.value_counts(normalize=True).sort_index()

    if len(temp) < len(Exp):
        temp = temp.reindex(ind).fillna(0)

    return ((temp - Exp) ** 2).mean()
