
import csv
import os
import locale
locale.setlocale(locale.LC_ALL, '')


def print_money(amt, dollar_sign=False, cents=False, pad=False):
    if amt is None:
        money = '$0.00'
    else:
        try:
            amt = float(amt)
        except ValueError:
            return amt
        money = locale.currency(amt, grouping=True)
    money = money.replace('$', '')
    if pad:
        deci = money.index('.')
        money = (pad - deci) * ' ' + money
    if dollar_sign:
        money = '$' + money
    if not cents:
        money = money.split('.')[0]
    return money


def augmented_slice(S):
    """
    Takes string of form:  :, n1:, :n2, n1:n2
    and returns a slice, with stop augmented if n2<0
    (i.e. -1 returns the whole thing, etc)
    """
    S = [x if len(x) else -1 for x in S.split(':')]
    S = [int(x) + int(int(x) < 0) for x in S]
    S[1] = None if not S[1] else S[1]
    return slice(S[0], S[1])


def scrub_csv(fn, legend_starts_with='Accounting Period', data_ends_with='Grand Total'):
    os.rename(fn, 'test_x_csv.csv')
    in_data = False
    with open('test_x_csv.csv', 'r') as fp_in:
        reader = csv.reader(fp_in)
        with open(fn, 'w') as fp_out:
            writer = csv.writer(fp_out)
            for row in reader:
                if row[0].strip().startswith(legend_starts_with):
                    in_data = True
                elif row[0].strip().startswith(data_ends_with):
                    break
                if in_data:
                    writer.writerow(row)
    os.remove('test_x_csv.csv')


def get_fund_directories(path=None):
    fund_to_dir = {}
    files = os.listdir(path)
    if path is None:
        path = os.getcwd()
    print(f"Checking {path} for fund directories.")
    for this_dir in files:
        try:
            fundno = int(this_dir.split('_')[0])
        except ValueError:
            continue
        print(f"\t Found {this_dir}")
        fund_to_dir[fundno] = this_dir
    return fund_to_dir


def split_csv(fn):
    funds = get_fund_directories()
    files_to_write = {}
    for fund, dirname in funds.items():
        files_to_write[fund] = {'fn': os.path.join(dirname, fn)}
        files_to_write[fund]['fp'] = open(files_to_write[fund]['fn'], 'w')
        files_to_write[fund]['writer'] = csv.writer(files_to_write[fund]['fp'])
        files_to_write[fund]['counter'] = 0

    with open(fn, 'r') as fp_in:
        reader = csv.reader(fp_in)
        for i, row in enumerate(reader):
            if not i:
                for vals in files_to_write.values():
                    vals['writer'].writerow(row)
            else:
                fundno = int(row[2].split()[0])
                files_to_write[fundno]['writer'].writerow(row)
                files_to_write[fundno]['counter'] += 1
    
    print(f"{i} total records.")

    for fundno in sorted(files_to_write):
        print(f"{files_to_write[fundno]['counter']:4d} entries to {files_to_write[fundno]['fn']}")
        files_to_write[fundno]['fp'].close()

def xls2csv(xlsfile, csvfile):
    import pandas
    read_file = pandas.read_excel(xlsfile)
    read_file.to_csv(csvfile, index = None, header=True, date_format='%Y/%m/%d')

def write_to_csv(csvout, data, header=None, **kwargs):
    """
    Write a csv file with header data and a header line
    """
    if not csvout.endswith('.csv'):
        csvout += '.csv'
    print("Writing {}".format(csvout))

    if len(list(kwargs.keys())):
        kw_hdr = [['Option settings']]
    else:
        kw_hdr = []
    for kw in kwargs.keys():
        kw_hdr.append([None, kw, kwargs[kw]])
    if header is not None and len(kw_hdr):
        csv_hdr = kw_hdr + [header]
    elif header is not None:
        csv_hdr = [header]
    elif header is None and len(kw_hdr):
        csv_hdr = kw_hdr
    else:
        csv_hdr = None

    if csv_hdr is not None:
        data = csv_hdr + data

    with open(csvout, 'w') as fp:
        writer = csv.writer(fp)
        for d in data:
            writer.writerow(d)
