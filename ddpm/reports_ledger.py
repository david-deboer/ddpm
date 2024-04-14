from . import utils_ledger as ul

def tex_dashboard(dashboard, name_date_format='%Y-%m-%d'):
    from pylatex import Document, Table, Tabular, Figure, Center, Command, VerticalSpace
    from pylatex.utils import bold, NoEscape
    from datetime import datetime

    pofp = dashboard.project.all_entries[dashboard.project.tasks[0]]
    now = datetime.now().strftime(name_date_format) 
    geometry_options = {"tmargin": "1.5cm", "lmargin": "2cm",
                        "bmargin": "1.5cm", "rmargin": "2cm"}
    doc = Document(geometry_options=geometry_options)
    doc.preamble.append(Command('title', dashboard.name))
    doc.preamble.append(Command('author', f"{pofp.begins.strftime('%Y-%m-%d')} - {pofp.ends.strftime('%Y-%m-%d')}"))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    # doc.append(VerticalSpace(NoEscape('-1cm')))

    # Summary
    if len(dashboard.sgrand): doc.append(NoEscape(r'\noindent ' + dashboard.sgrand + r'\newline'))
    if len(dashboard.sdept): doc.append(dashboard.sdept)
    with doc.create(Figure(position='h!')) as bar_chart:
        bar_chart.add_image('fig_chart.png', width='250px')
        bar_chart.add_caption('Category budgets and expenditures.')
    with doc.create(Table(position='h!')) as table:
        table.add_caption("Category Summary Table")
        with doc.create(Center()):
            with doc.create(Tabular('|l|r|r|r|')) as tabular:
                tabular.add_hline()
                tabular.add_row((bold("Category"), bold("Budget"), bold("Expenditures"), bold("Balance")))
                tabular.add_hline()
                for row in dashboard.table_data:
                    tabular.add_row((row[0],
                                    ul.print_money(row[1]),
                                    ul.print_money(row[3]),
                                    ul.print_money(row[2])))
                    tabular.add_hline()
    with doc.create(Figure(position='h!')) as bar_chart:
        bar_chart.add_image('fig_ledger.png', width='200px')
        bar_chart.add_caption('Period of performance.')
    # # Rates
    # with doc.create(Figure(position='h!')) as rate:
    #     rate.add_image('rate.png', width='400px')
    #     rate.add_caption('Category rates.')
    # # Budget/expenditures all categories
    # with doc.create(Table(position='h!')) as be_table:
    #     be_table.add_caption("Budgets, expenditures and remaining - all included categories")
    #     with doc.create(Center()):
    #         with doc.create(Tabular('l r')) as tabular:
    #             for mlab in ['Sponsor budget', 'Expenditures total',
    #                             'Remaining amount', 'Average rate']:
    #                 _money = ul.print_money(dashboard.group_detail_info.chart[mlab])
    #                 tabular.add_row((mlab, _money))
    # # Budget/expenditures UCB expenditures
    # with doc.create(Table(position='h!')) as be_table:
    #     be_table.add_caption("Budgets, expenditures and remaining - UCB")
    #     with doc.create(Center()):
    #         with doc.create(Tabular('l r')) as tabular:
    #             for mlab in ['UCB budget', 'UCB expend', 'UCB remain']:
    #                 _money = ul.print_money(dashboard.group_detail_info.chart[mlab])
    #                 tabular.add_row((mlab, _money))
    # # Last figures
    # with doc.create(Figure(position='h!')) as cumu:
    #     cumu.add_image('cumulative.png', width='400px')
    #     cumu.add_caption('Category cumulative.')
    # with doc.create(Figure(position='h!')) as daily:
    #     daily.add_image('daily.png', width='400px')
    #     daily.add_caption('Category daily.')
    doc.generate_pdf(f'report{dashboard.ledger.fund}_{now}', clean_tex=False)
