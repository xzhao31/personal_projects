# this file contains functions to solve formulas in conjunctive normal form (CNF),
# and uses it to solve a sudoku board of any given size

import sys
import typing
import doctest

sys.setrecursionlimit(10_000)


def reduce_formula(formula,c):
    """
    given a longer formula and a condition c, reduce the formula to a simpler version
    *if there is an empty list in the formula, then it is invalid!
    """
    reduced=[]
    for clause in formula:
        if c in clause:
            pass
        elif (c[0],not c[1]) in clause:
            new_condition=[condition for condition in clause if condition!=(c[0],not c[1])]
            if new_condition:
                reduced.append(new_condition)
            else:
                reduced.append([])
        else:
            reduced.append(clause)
    return reduced


def satisfying_assignment(formula):
    """
    Find a satisfying assignment for a given CNF formula.
    Returns that assignment if one exists, or None otherwise.

    >>> satisfying_assignment([])
    {}
    >>> x = satisfying_assignment([[('a', True), ('b', False), ('c', True)]])
    >>> x.get('a', None) is True or x.get('b', None) is False or x.get('c', None) is True
    True
    >>> satisfying_assignment([[('a', True)], [('a', False)]])
    """
    #eliminate unit clauses
    unit_clauses={}
    exist_unit_clauses=True
    while exist_unit_clauses:
        exist_unit_clauses=False
        for clause in formula:
            if len(clause)==1:
                this_condition=clause[0]
                formula=reduce_formula(formula,this_condition)
                unit_clauses[this_condition[0]]=this_condition[1]
                exist_unit_clauses=True
                break #if we encounter a unit clause, update the new formula and start over

    #base case: success
    if len(formula)==0:
        return {} | unit_clauses

    #failure
    if [] in formula:
        return None
    
    #assume first literal
    this_condition=formula[0][0]
    #recursively compute other variables
    this_reduced=reduce_formula(formula,this_condition)
    result=satisfying_assignment(this_reduced)
    if result is not None:
        return result | {this_condition[0]: this_condition[1]} | unit_clauses

    #if doesn't work, assume NOT first literal
    this_condition=(formula[0][0][0],not formula[0][0][1])
    #recursively compute other variables
    this_reduced=reduce_formula(formula,this_condition)
    result=satisfying_assignment(this_reduced)
    if result is not None:
        return result | {this_condition[0]: this_condition[1]} | unit_clauses


def subgrid(sub_n,i,j):
    """
    given the (i,j)th subgrid of side length sub_n, return a set of coordinates in that subgrid
    """
    coords=set()
    for row in range(sub_n*i,sub_n*(i+1)):
        for col in range(sub_n*j,sub_n*(j+1)):
            coords.add((row,col))
    return coords


def sudoku_board_to_sat_formula(sudoku_board):
    """
    Generates a SAT formula that, when solved, represents a solution to the
    given sudoku board.  The result should be a formula of the right form to be
    passed to the satisfying_assignment function above.

    representation is (value,row,col)
    """
    n=len(sudoku_board)
    sub_n=int(n**0.5)
    formula=[]

    #unit clauses of pre-filled numbers
    for row in range(n):
        for col in range(n):
            if sudoku_board[row][col]!=0:
                formula.append([((sudoku_board[row][col],row,col),True)])
    
    #1 per row
    for val in range(1,n+1):
        for row in range(n):
            at_least=[]
            for col1 in range(n):
                at_least.append(((val,row,col1),True))
                for col2 in range(n):
                    if col1<col2:
                        formula.append([((val,row,col1),False),((val,row,col2),False)]) #at most 1
            formula.append(at_least) #at least 1
        
    #1 per col
    for val in range(1,n+1):
        for col in range(n):
            at_least=[]
            for row1 in range(n):
                at_least.append(((val,row1,col),True))
                for row2 in range(n):
                    if row1<row2:
                        formula.append([((val,row1,col),False),((val,row2,col),False)]) #at most 1
            formula.append(at_least) #at least 1
    
    #1 per subgrid
    for val in range(1,n+1):
        for sub_row in range(sub_n):
            for sub_col in range(sub_n):
                at_least=[]
                for row1,col1 in subgrid(sub_n,sub_row,sub_col):
                    at_least.append(((val,row1,col1),True))
                    for row2,col2 in subgrid(sub_n,sub_row,sub_col):
                        if row1<row2 and col1<col2:
                            formula.append([((val,row1,col1),False),((val,row2,col2),False)]) #at most 1
                formula.append(at_least) #at least 1
    
    #1 in each cell
    for row in range(n):
        for col in range(n):
            at_least=[]
            for val1 in range(1,n+1):
                at_least.append(((val1,row,col),True))
                for val2 in range(1,n+1):
                    if val1<val2:
                        formula.append([((val1,row,col),False),((val2,row,col),False)]) #at most 1
            formula.append(at_least) #at least 1
    
    #done!
    return formula


def assignments_to_sudoku_board(assignments, n):
    """
    Given a variable assignment as given by satisfying_assignment, as well as a
    size n, construct an n-by-n 2-d array (list-of-lists) representing the
    solution given by the provided assignment of variables.

    If the given assignments correspond to an unsolveable board, return None
    instead.
    """
    if assignments is None:
        return None

    board=[]
    for row in range(n):
        entry=[]
        for col in range(n):
            entry.append(0)
        board.append(entry)
    
    for assignment,truth in assignments.items():
        if truth:
            board[assignment[1]][assignment[2]]=assignment[0]

    return board
        


if __name__ == "__main__":
    import doctest

##    _doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
##    doctest.testmod(optionflags=_doctest_flags)
