################################################################################
#  Digon                                                                       #
#  A graph-based programming language for naturally concurrent and             #
#  well-structured code.                                                       #
#                                                                              #
#  Created by Sebastian Coates and John Tagliaferro at Tufts University.       #
#                                                                              #
#  transpiler.py                                                               #
#  Transpiles Digon into equivalent Go.                                        #
#                                                                              #
#  Copyright 2018 Sebastian Coates and John Tagliaferro.                       #
#                                                                              #
#  Digon is free software: you can redistribute it and/or modify               #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation, either version 3 of the License, or           #
#  (at your option) any later version.                                         #
#                                                                              #
#  Digon is distributed in the hope that it will be useful,                    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with Digon.  If not, see <http://www.gnu.org/licenses/>.              #
################################################################################

# Changes Digon syntax to Go equivalent, or adds appropriate spacing
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       ccfg - full colored control flow graph
#
def change_basic_syntax(node, ccfg):
        sourcecode = node.sourceCode
        nodes = ccfg.nodes

        #ensure appropriate whitespace, simple syntax changes
        explicitChildren = set([token for token in sourcecode if token in node.neighbors])

        for i, token in enumerate(sourcecode):
                if token == 'in':
                        if sourcecode[i - 1] == ")":
                                sourcecode[i - 1] = ""
                                if sourcecode[i - 5] == "(":
                                        sourcecode[i - 5] = ""
                        sourcecode[i] = " := range "
                elif token == "println":
                        sourcecode[i] = "fmt.Println"
                elif token == 'if':
                        sourcecode[i] = 'if '
                elif token == 'for':
                        sourcecode[i] = 'for '
                elif token == 'float':
                        sourcecode[i] = 'float64'
                elif token == 'map' and sourcecode[i - 2] == ':': #map delcaration
                        sourcecode[i] = "make(map"
                        sourcecode[i + 1] = "["
                        sourcecode[i + 3] = ']'
                        sourcecode[i + 5] = ")"

# Links node to buffer function
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       i - current index in source code
#       param - parameter sent to channel
#
def overwrite_dest(sourcecode, i, param):
        sourcecode[i - 1] = "channel"
        sourcecode[  i  ] = '<'
        sourcecode[i + 1] = '-'
        sourcecode[i + 2] = param
        sourcecode[i + 3] = "" #replace (
        sourcecode[i + 4] = "" #replace )

# Links node to buffer function
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       i - current index in source code
#       destTypes - channel type for each destination 
#       destinations - list of destination links in current function 
#       leftindex - index of lvalue string
#       param - parameter sent to channel
#
def overwrite_node_link(sourcecode, i, destTypes, destinations, leftindex, param):
        fname = sourcecode[i + 2] #node name
        sourcecode[i - 1] = fname
        if sourcecode[i - 1] == "length":
                sourcecode[i - 1] = "len"
        sourcecode[i] = '('
        if destTypes.get(fname) != None:
                param += ', ' + fname + "Channel"

        sourcecode[i + 1] = param
        sourcecode[i + 2] = ')'
        i += 3
        while sourcecode[i] != ')':
                sourcecode[i] = ""
                i += 1
        sourcecode[i] = ""
        i += 1

        if sourcecode[i] == '=': #check if assignment or pass-on node
                if sourcecode[i + 3] != '(': #assignment
                        sourcecode[leftindex] = sourcecode[i + 2] + " = " + sourcecode[leftindex]
                        sourcecode[i] = ""
                        sourcecode[i + 1] = ""
                        sourcecode[i + 2] = ""
                        i += 3
                else:
                        sourcecode[leftindex] = "go " + sourcecode[leftindex]
                        while sourcecode[i] != ")":
                                if sourcecode[i + 1] == "(":
                                        if destinations.get(sourcecode[i]) == None:
                                                destinations[sourcecode[i]] = []

                                        sourcecode[leftindex] = fname + "Channel := make(chan " \
                                        + destTypes[fname] + ")\n" + sourcecode[leftindex]
                                        
                                        destinations[sourcecode[i]].append(fname + "Channel")
                                sourcecode[i] = ""
                                i += 1
                        sourcecode[i] = ""

# Resolves dest and other node linking to go function calls 
# Params:
#       i - current index in source code
#       token - current token (at sourcecode[i])
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       destTypes - channel type for each destination 
#       destinations - list of destination links in current function 
#
# WARNING: this function relies on semicolons in sourcecode 
#
def process_function(i, token, sourcecode, destTypes, destinations):
        leftindex = i - 1 #index of lval
        j = 1
        param = "" 
        
        #Determine full parameters for node (could be expression, tuple)
        while sourcecode[i - j] != ';' and sourcecode[i - j] != '}': 
                param = sourcecode[i - j] + param
                sourcecode[i - j] = ""
                j += 1

        if sourcecode[i + 2] == 'dest':
                overwrite_dest(sourcecode, i, param)
        else: 
                overwrite_node_link(sourcecode, i, destTypes, destinations,\
                        leftindex, param)
                
# Handles current token in node source code
# Params:
#       i - current index in source code
#       token - current token (at sourcecode[i])
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       ccfg - full colored control flow graph
#       destinations - list of destination links in current function 
#
# WARNING: this function relies on semicolons in sourcecode 
#
def process_token(i, token, sourcecode, ccfg, destinations):
        destTypes = ccfg.channels

        if token == '=' and sourcecode[i + 1] == ">":
                process_function(i, token, sourcecode, destTypes, destinations)
        else:
                pass

# Writes buffer function (end result of concurrent nodes' destinations)
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       destinations - list of destination links in current function 
#
# WARNING: this function relies on semicolons in sourcecode 
#
def write_buffer_function(sourcecode, destinations):
        for dest in destinations: #
                funcode = "\n" + dest + "("
                for i, channel in enumerate(destinations[dest]):
                        funcode += channel
                        if i != len(destinations[dest]) - 1:
                                funcode += ", "
                funcode += ")\n"
                sourcecode.append(funcode)

# Changes Resolves node linking to Go function calls as appropriate
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
#       ccfg - full colored control flow graph
#
def transpile_function_calls(node, ccfg):
        sourcecode = node.sourceCode
        nodes = ccfg.nodes
        destinations = {}

        for i, token in enumerate(sourcecode):
               process_token(i, token, sourcecode, ccfg, destinations)

        #Writes function call to buffer function if needed        
        write_buffer_function(sourcecode, destinations)


################################## INTERFACE ###################################
# Transpiles Digon source to equivalent Go source
# Params:
#       sourcecode - Parsed Digon source code by line (list of string lists)
# 
# Returns: 
#       transpiled - Transpiled code in same form
#
def transpile_to_go(node, ccfg):
        change_basic_syntax(node, ccfg)        
        transpile_function_calls(node, ccfg)