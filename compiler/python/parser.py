################################################################################
#  Digon                                                                       #
#  A graph-based programming language for naturally concurrent and             #
#  well-structured code.                                                       #
#                                                                              #
#  Created by Sebastian Coates and John Tagliaferro at Tufts University.       #
#                                                                              #
#  parser.py                                                                   #
#  Contains code for parsing lexed Digon source files.                         #
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

from errors import *
from node   import *

builtinFunctions = ['length', 'println']


# Initialize nodes with names and sourcecode
# Params:
#       nodeIndices - indices of node keyword
#       lexedFile - content of source file as list of tokens
#       nodes - empty list of node objects to be added to
#       names - list of names of nodes
#
def initialize_nodes(nodeIndices, lexedFile, nodes, names):
    for i in range(len(nodeIndices) - 1):
        n = nodeIndices[i];
        nod = create_node(lexedFile[n + 1]);
        names.append(nod.name);
        
        if lexedFile[n + 2] == "<":        # node has params
            paramS = n + 5;                 # strt of params
            params = [];
            end = lexedFile[paramS:].index(")");        # where params end

            n = end + paramS + 2;       # set n to first index of code
            while True:                                 # get up to last param
                if "," in  lexedFile[paramS:paramS + end]:      
                    comma = lexedFile[paramS:paramS + end].index(",");
                    params.append(" ".join(lexedFile[paramS:paramS + comma]));
                    paramS += comma + 1;
                    end -= (comma + 1);
                else:
                    break;

            # get last param
            params.append(" ".join(lexedFile[paramS:paramS + end]));
            nod.params = params;
        else:
            nod.params = "";
            n += 3;

        nod.sourceCode = lexedFile[n:nodeIndices[i + 1] - 1];

        nodes.append(nod);


# Define ancestor / descendant (neighbor) relationships between nodes
# Params:
#       nodeIndices - indices of node keyword
#       lexedFile - content of source file as list of tokens
#       nodes - empty list of node objects to be added to
#       names - list of names of nodes
#
def define_relationships(nodes):
    node_dict = {}
    for nod in nodes:
        node_dict[nod.name] = nod
        nod.neighbors = set()
        
    for nod in nodes:
        li = nod.sourceCode;
        i = 0;
        while i < len(li):
            if li[i] == "=" and li[i + 1] == ">" and li[i + 2] != 'dest':
                neighbor = li[i + 2]
                nod.neighbors.add(neighbor)
                if neighbor not in builtinFunctions:
                    node_dict[neighbor].ancestors.add(nod.name) #err on built-in funcs
                
                while(li[i] != ')'): #Parser guarantees this will happen
                    i += 1

                if neighbor not in builtinFunctions:
                    
                    if li[i + 1] == "=" and li[i + 2] == ">" \
                        and li[i + 3] != 'dest' and li[i + 4] == '(':
                        
                            node_dict[neighbor].dest = li[i + 3];
                            destParam = li[i + 5]
                            for param in node_dict[li[i + 3]].params:
                                if destParam in param:
                                    paramType = param.split()[1:]
                                    for part in paramType:
                                        if part == 'float':
                                            part += '64'
                                        node_dict[neighbor].destType += part 

                            node_dict[li[i + 3]].ancestors.add(neighbor)
                            i += 1

            i += 1;


# Prints all node info
# Params:
#       nodes - list of node objects
#
#
def print_nodes(nodes):
    for nod in nodes:
        print(nod.name)

        print('Params:\t', end="")
        print(nod.params)

        print('sourceCode:\t', end="")
        print(nod.sourceCode)

        print('neighbors:\t', end="")
        print(nod.neighbors)
    
        print('ancestors:\t', end="")
        print(nod.ancestors)
    
        print('dest:\t', end="")
        print(nod.dest)
    
        print('destType:\t', end="")
        print(nod.destType)

        print()


################################## INTERFACE ###################################

# Parses file, reports warnings and errors.
# Params:
#       lexedFile - lexed plaintext of file as list of tokens 
# 
# Returns: 
#       parsed - lexed, parsed plaintext as dictionary {node ID --> node struct}
#
def parse(lexedFile):
    lexedFile =  [j for i in lexedFile for j in i];
    names = [];
    nodes = [];
    nodeIndices = [i for i, x in enumerate(lexedFile) if x == "node"];
    length = len(lexedFile);
    nodeIndices.append(length);

    initialize_nodes(nodeIndices, lexedFile, nodes, names)
    define_relationships(nodes)
    
    #print_nodes(nodes)
    return nodes;