# Generated from scripts/gen_acl.py

Academic_Wages = ['58012', '50046', '50100', '50200', '50211', '50212', '50215', '50240', '50241',
                  '50242', '50289']
Staff_Wages = ['58019', '51010', '51015', '51029', '51200', '51210', '51231', '51232', '51289',
               '51300', '58020', '58026']
Other_Employee_Compen = ['52000', '52010', '52011', '52012', '52013', '52020', '52040', '52050', '52051']
Retirement_Benefits = ['53000', '53060', '53070', '53080', '53090', '53100', '53105', '53110',
                       '53200', '53300', '53400', '53410', '53411', '53413', '53420', '53421',
                       '53430', '53431', '53500', '53501', '53502', '53600', '53601', '53700',
                       '53701', '53702', '53703', '53704', '53705', '53706', '53707', '53708',
                       '53709', '53710', '53711', '53712', '53800', '53801', '53802', '53803',
                       '53900', '53910', '53921', '53922', '53933', '53934', '53940', '53941',
                       '53942', '53943', '53950', '53951', '53960', '53990', '53998']
Computer_Equip_Inven = ['54100', '54110', '54120', '54121', '54130']
Equip_Inventorial = ['54200', '54210', '54211', '54212', '54213', '54214', '54215', '54216',
                     '54217', '54218', '54220', '54221', '54231', '54232', '54240', '54241',
                     '54242', '54243', '54244', '54245', '54250', '54251', '54252', '54260']
General_Supplies_Other = ['55000', '55010', '55011', '55012', '55013', '55014', '55015', '55016',
                          '55017', '55018', '55060', '55061', '58015', '55020', '55021', '55022']
General_Office_Supplies = ['55030', '55031', '55032']
General_Supplies_X = ['55040', '55041', '55042', '55043', '55044', '55045', '55046', '55047',
                      '55048', '55049']
General_Supplies_Food = ['55050', '55051', '55052', '55053', '55054', '55056', '55059']
General_Supplies = General_Supplies_Other + General_Office_Supplies + General_Supplies_X + General_Supplies_Food
Computing_Supplies = ['55100', '55101']
Comp_Equip_Non_Inventor = ['55200', '55201', '55211', '55221']
Equip_Non_Inventorial = ['55300', '55301', '55302', '55303', '55304', '55309', '55311', '55312',
                         '55313', '55314', '55319', '55321', '55322', '55323', '55324', '55329', '55399']
Comp_Serv_Software = ['56000', '56010', '56011', '56012', '56013', '56020', '56021', '56022',
                      '56023', '56024', '56030', '56031']
Communications = ['56100', '56110', '56111', '56120', '56121', '56130', '56190']
Maint_Contract_Serv = ['56200', '56210', '56220', '56230', '56240', '56290']
Rents_Utilities = ['56300', '56310', '56311', '56312', '56313', '56320', '56330', '56331', '56340',
                   '56341', '56342', '56349', '56350', '56351', '56352', '56353', '56354', '56398']
Publications_Media = ['56400', '56410', '56411', '56413', '56420', '56421', '56422', '56423', '56430', '56440']
Transportation = ['56500', '56510', '56520', '56530']
Other_Serv_Non_Computer = ['56600', '56610', '56611', '56620', '56621', '56622', '56623', '56624',
                           '56625', '56626', '56627', '56629', '56630', '56631', '56632', '56633',
                           '56634', '56635', '56636', '56638', '56640']
Non_Employee_Payments = ['56700', '56710', '56711', '56712', '56713', '56714', '56715', '58016',
                         '58022', '58023', '58024', '58025', '56720', '56721', '56722', '56723',
                         '56724', '56725', '56726', '56727', '56728', '56729', '58030', '56731']
Conf_Mtgs_Training_Events = ['57000', '58021', '57001', '57002', '57003', '57004', '57005', '57006', '57007']
Travel_Domestic = ['57210', '57211', '57212', '57213', '57214', '57215', '57216']
Travel_Foreign = ['57220', '57221', '57222', '57223']
Travel_Other = ['57230', '57232', '57233', '57239']
Travel = Travel_Domestic + Travel_Foreign + Travel_Other
Misc_Expense_577XX = ['57300', '57301', '57302', '57303', '57304', '57305', '57306', '58010',
                      '58018', '58027', '58028', '57310', '57311', '57312', '57313', '57314',
                      '57315', '57316', '57317', '57318', '57320', '57321', '57322', '57323',
                      '57324', '57325', '57326', '57327', '57328', '57329', '57330', '57331',
                      '57332', '57334', '57335', '57340', '57341', '57342', '57350', '57351',
                      '57352', '57353', '57354', '57355', '57358', '57365', '57366', '57371',
                      '57375', '57360', '57361', '57369', '57370', '57372', '57373', '57378',
                      '57379', '57380', '57381', '57382', '57383', '57384', '57385', '57386',
                      '57387', '57388', '57389', '57780', '57781', '57390', '57399', '57710', '57720']
Pymts_Students_Stud_Aid = ['57400', '58017', '57410', '57411', '57412', '57413', '57414', '57415',
                           '57420', '57421', '57422', '57423', '57424', '57425', '57430', '57431',
                           '57440', '57441', '57442', '57443', '57444', '57445', '57450', '57455',
                           '57456', '57490']
Impairment_of_Cap_Assets = ['57510', '57511', '57512', '57513', '57514', '57515', '57516', '57517',
                            '57518', '57519', '57520', '57521', '57550', '57560', '57561', '57570', '57571']
C_G_Sub_Awards = ['57800', '57810', '57811', '57819', '58013', '58014', '57820', '57821', '57830',
                  '57831', '57840', '57841', '57850', '57851', '57860', '57861', '57870', '57871',
                  '57880', '57881', '57890', '57891', '57895', '57896']
Intercampus = ['92507', '92504', '98002']
C_G_Sponsor_Direct_Cost = ['57901']
C_G_Spnsr_Indirect_Cost = ['57900', '57990', '57998', '58011']
Unallocated = ['58000', '58001']
Reappropriation = ['58100']
Fund_Advance_Unalloc = ['58200']
Recharge_Income = ['58029', '59000']
Control_Unit_Budget_Provisions = ['59990', '59991', '59992', '59993', '59994', '59998']

account_types = ['Academic_Wages', 'Staff_Wages', 'Other_Employee_Compen', 'Retirement_Benefits',
                 'Computer_Equip_Inven', 'Equip_Inventorial', 'General_Supplies', 'Computing_Supplies',
                 'Comp_Equip_Non_Inventor', 'Equip_Non_Inventorial', 'Comp_Serv_Software',
                 'Communications', 'Maint_Contract_Serv', 'Rents_Utilities', 'Publications_Media',
                 'Transportation', 'Other_Serv_Non_Computer', 'Non_Employee_Payments',
                 'Conf_Mtgs_Training_Events', 'Travel', 'Misc_Expense_577XX', 'Pymts_Students_Stud_Aid',
                 'Impairment_of_Cap_Assets', 'Intercampus', 'C_G_Sub_Awards', 'C_G_Sponsor_Direct_Cost',
                 'C_G_Spnsr_Indirect_Cost', 'Unallocated', 'Reappropriation', 'Fund_Advance_Unalloc',
                 'Recharge_Income', 'Control_Unit_Budget_Provisions']

sub_account_types = ['Travel_Domestic', 'Travel_Foreign', 'Travel_Other',
                     'General_Supplies_Other', 'General_Office_Supplies',
                     'General_Supplies_X', 'General_Supplies_Food']

nsf = {'staff': Academic_Wages + Staff_Wages + Other_Employee_Compen + Retirement_Benefits,
       'equip': Computer_Equip_Inven + Equip_Inventorial + Comp_Equip_Non_Inventor + Equip_Non_Inventorial,
       'travel': Conf_Mtgs_Training_Events + Travel,
       'other': (General_Supplies + Computing_Supplies + Comp_Serv_Software + Communications +
                 Maint_Contract_Serv + Rents_Utilities + Publications_Media +
                 Transportation + Other_Serv_Non_Computer + Misc_Expense_577XX +
                 Pymts_Students_Stud_Aid + Impairment_of_Cap_Assets +
                 C_G_Sponsor_Direct_Cost + Unallocated + Reappropriation +
                 Fund_Advance_Unalloc + Recharge_Income + Control_Unit_Budget_Provisions +
                 Non_Employee_Payments),
       'subs': Intercampus + C_G_Sub_Awards, 
       'indirect' : C_G_Spnsr_Indirect_Cost}
gbmf = nsf
si = nsf


sra = {'staff': Academic_Wages + Staff_Wages + Other_Employee_Compen + Retirement_Benefits,
       'equip': Computer_Equip_Inven + Equip_Inventorial + Comp_Equip_Non_Inventor + Equip_Non_Inventorial,
       'travel': Conf_Mtgs_Training_Events + Travel,
       'other': (General_Supplies + Computing_Supplies + Comp_Serv_Software + Communications +
                 Maint_Contract_Serv + Rents_Utilities + Publications_Media +
                 Transportation + Other_Serv_Non_Computer + Misc_Expense_577XX +
                 Pymts_Students_Stud_Aid + Impairment_of_Cap_Assets +
                 C_G_Sponsor_Direct_Cost + Unallocated + Reappropriation +
                 Fund_Advance_Unalloc + Recharge_Income + Control_Unit_Budget_Provisions),
       'contracts': Non_Employee_Payments,
       'subs': Intercampus + C_G_Sub_Awards,
       'indirect': C_G_Spnsr_Indirect_Cost}

gift = {'supplies': General_Supplies,
        'meetings': Conf_Mtgs_Training_Events,
        'domestic': Travel_Domestic,
        'foreign': Travel_Foreign,
        'other_travel': Travel_Other}

# Home
energy = ['gas', 'solar', 'power']
living = ['water', 'garbage', 'grocery', 'retail', 'internet', 'auto']
entertainment = ['restaurant', 'admission', 'subscription']
other = ['other', 'dmv', 'rent', 'health', 'education', 'transportation']
finance = ['transfer', 'credit', 'mortgage', 'salary', 'insurance', 'atm', 'loan', 'interest', 'tax']
work = ['reimbursement']

boa = {'energy': energy, 'living': living, 'entertainment': entertainment, 'other': other, 'finance': finance, 'work': work}