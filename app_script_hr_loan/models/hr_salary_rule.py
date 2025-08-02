
from odoo import api, fields, models

class Contract(models.Model):
    _inherit = "hr.contract"

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        for rec in self :
            structures = rec.mapped('structure_type_id.struct_ids')
            if not structures:
                return []
            return structures


class PayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.id.rule_ids._recursive_search_of_rules()
            
        return all_rules

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        return [(rule.id, rule.sequence) for rule in self] 


    def compute_allowed_deduct_amount(self, contract_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        blacklist = []
        result_dict = {}
        rules_dict = {}
        categories = BrowsableObject(contract_id.employee_id.id, {}, self.env)
        rules = BrowsableObject(contract_id.employee_id.id, rules_dict, self.env)
        baselocaldict = {'categories': categories, 'rules': rules, }
        structure_ids = contract_id.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()

        falg = False
        for x in rule_ids:
            if x[0] == self.id:
                falg =True
        if not falg:
            rule_ids.append((self.id,self.sequence))
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        contract =contract_id
        employee = contract.employee_id
        localdict = dict(baselocaldict, employee=contract_id.employee_id, contract=contract_id)
        if not self._satisfy_condition(localdict) or self.id in rule_ids:
            return 0.0

        for rule in sorted_rules:
            key = rule.code + '-' + str(contract.id)
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 100
            localdict['contract'] = contract_id
            localdict['employee'] = contract_id.employee_id
            if (not rule._satisfy_condition(localdict) or rule.id   in rule_ids):
                amount =  0.0
                qty= rate = 1
            else :
                amount, qty, rate = rule._compute_rule(localdict)

            previous_amount = rule.code in localdict and localdict[rule.code] or 0.0

            tot_rule = amount * qty * rate / 100.0
            localdict[rule.code] = tot_rule
            rules_dict[rule.code] = rule
            localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
            result_dict[rule.code] = {
                    'salary_rule_id': rule.id,
                    'contract_id': contract.id,
                    'name': rule.name,
                    'code': rule.code,
                    'category_id': rule.category_id.id,
                    'sequence': rule.sequence,
                    'condition_select': rule.condition_select,
                    'condition_python': rule.condition_python,
                    'condition_range': rule.condition_range,
                    'condition_range_min': rule.condition_range_min,
                    'condition_range_max': rule.condition_range_max,
                    'amount_select': rule.amount_select,
                    'amount_fix': rule.amount_fix,
                    'amount_python_compute': rule.amount_python_compute,
                    'amount_percentage': rule.amount_percentage,
                    'amount_percentage_base': rule.amount_percentage_base,
                    'amount': tot_rule,
                    'employee_id': contract.employee_id.id,
                    'quantity': qty,
                    'rate': rate,
                }
            if rule.id == self.id:

                return result_dict[self.code]['amount']
            else:
                blacklist += [id for id, seq in rule._recursive_search_of_rules()]
        return result_dict[self.code]['amount']

