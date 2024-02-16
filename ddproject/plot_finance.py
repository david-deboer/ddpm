import matplotlib.pyplot as plt
import numpy as np


def chart(x, y, label, norm=1.0, width=0.65,  xlabel=None, ylabel=None,
             add_legend=True, save_it=False):
    ind = list(range(len(x)))
    if isinstance(label, str):
        if len(x) != len(y):
            print("Dimensions wrong for bar chart.")
            return
        label = [label]
        plty = [np.array(y)]
    else:
        if len(y) != len(label) or len(x) != len(y[0]):
            print("Dimensions wrong for stacked bar chart.")
            return
        plty = []
        for this_group in y:
            plty.append(np.array(this_group) / norm)
    sumy = np.zeros(len(x))

    for this_label, this_plot in zip(label, plty):
        plt.bar(ind, this_plot, width, label=this_label, bottom=sumy)
        sumy += this_plot

    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    plt.xticks(ind, x)
    if add_legend:
        plt.legend()
    if save_it:
        if isinstance(save_it, str):
            plt.savefit(save_it)
        else:
            plt.savefig('bar_chart.png')

def tex_dashboard(self, ledger):
    from pylatex import Document, Table, Tabular, Figure, Center, Command
    from pylatex.utils import bold, NoEscape
    from datetime import datetime

    now = datetime.now().isoformat(timespec='minutes').replace(':', '')
    geometry_options = {"tmargin": "1.5cm", "lmargin": "2cm",
                        "bmargin": "1.5cm", "rmargin": "2cm"}
    doc = Document(geometry_options=geometry_options)
    doc.preamble.append(Command('title', self.ledger.plot_title))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    # Summary
    _money = ledger.LU.print_money(self.group_detail_info.grand)
    doc.append("This report summarizes budgets for {}.  ".format(self.ledger.plot_title))
    doc.append(f"Total expenditures in all categories is {_money}.")
    diff = self.group_detail_info.grand - self.group_detail_info.chart['Expenditures total']
    if abs(diff) > 1.0:
        _money = ledger.LU.print_money(self.group_detail_info.chart['Expenditures total'])
        doc.append(f"Total expenditures in included categories is {_money}, ")
        _money = ledger.LU.print_money(diff)
        doc.append(f"which leaves {_money} in other categories.\n\n")
    with doc.create(Figure(position='h!')) as bar_chart:
        bar_chart.add_image('bar_chart.png', width='400px')
        bar_chart.add_caption('Category budgets and expenditures.')
    with doc.create(Table(position='h!')) as table:
        table.add_caption("Category Summary Table")
        with doc.create(Center()):
            with doc.create(Tabular('l|r|r')) as tabular:
                tabular.add_hline()
                tabular.add_row((bold("Category"), bold("Expenditures"), bold("Remaining")))
                tabular.add_hline()
                for row in self.group_detail_info.cat:
                    tabular.add_row((row.group,
                                    ledger.LU.print_money(row.subtotal),
                                    ledger.LU.print_money(row.remaining)))
                    tabular.add_hline()
    # Rates
    with doc.create(Table(position='h!')) as rate_table:
        rate_table.add_caption("Monthly rates")
        with doc.create(Center()):
            with doc.create(Tabular('l r')) as tabular:
                tabular.add_row(("Group", "Monthly Average"))
                tabular.add_hline()
                for group, ave in self.ledger.rates.items():
                    tabular.add_row(group, ledger.LU.print_money(ave))
    with doc.create(Figure(position='h!')) as rate:
        rate.add_image('rate.png', width='400px')
        rate.add_caption('Category rates.')
    # Budget/expenditures all categories
    with doc.create(Table(position='h!')) as be_table:
        be_table.add_caption("Budgets, expenditures and remaining - all included categories")
        with doc.create(Center()):
            with doc.create(Tabular('l r')) as tabular:
                for mlab in ['Sponsor budget', 'Expenditures total',
                                'Remaining amount', 'Average rate']:
                    _money = ledger.LU.print_money(self.group_detail_info.chart[mlab])
                    tabular.add_row((mlab, _money))
    # Budget/expenditures UCB expenditures
    with doc.create(Table(position='h!')) as be_table:
        be_table.add_caption("Budgets, expenditures and remaining - UCB")
        with doc.create(Center()):
            with doc.create(Tabular('l r')) as tabular:
                for mlab in ['UCB budget', 'UCB expend', 'UCB remain']:
                    _money = ledger.LU.print_money(self.group_detail_info.chart[mlab])
                    tabular.add_row((mlab, _money))
    # Last figures
    with doc.create(Figure(position='h!')) as cumu:
        cumu.add_image('cumulative.png', width='400px')
        cumu.add_caption('Category cumulative.')
    with doc.create(Figure(position='h!')) as daily:
        daily.add_image('daily.png', width='400px')
        daily.add_caption('Category daily.')
    doc.generate_pdf(f'report{self.ledger.fund_number}_{now}', clean_tex=False)
