# the numbers at the end of the commends in the grammar reference the size of the chunk pattern. Except for exception cases,
# higher-numbered chunks need to go above lower ones so smaller chunks don't match before bigger ones.
command_structures = r"""

                # variations on 'take all out-of/from-in backpack but knife'
                FVB-OBJ/ALL-OUT-FROM-IN-CONT: {<FVB>(<(OBJ|CONT)>+|<ALL>)<OUT><FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}  # 8
                FVB-OBJ/ALL-OUT-OF/FROM-CONT: {<FVB>(<(OBJ|CONT)>+|<ALL>)<OUT><(OF|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 7
                FVB-OBJ/ALL-IN/FROM-CONT: {<FVB>(<(OBJ|CONT)>+|<ALL>)<(IN|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 6
                FVB-OBJ/ALL-FROM-IN-CONT: {<FVB>(<(OBJ|CONT)>+|<ALL>)<FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}

                USE-OBJ-TO-FVB-ACT/OBJ: {<USE><OBJ><TO><FVB><(ACT|OBJ)>}  # use knife to attack troll / use key to open door (custom function) 5
                FVB-OBJ-AT-ACT: {<FVB><OBJ>+<AT><ACT>}  # throw lantern at troll 4

                FVB-ACT/OBJ-WITH-OBJ: {<(FVB|VB)><(ACT|OBJ)><WITH><OBJ>}  # attack troll with knife 4

                FVB-ACT/OBJ-WITH-POBJ: {<FVB><(ACT|OBJ)><WITH><POBJ>}  # 4

                FVB-ALL-BUT-OBJ: {<FVB><ALL><BUT><(OBJ|CONT)>}  # drop everything but egg 4
                FVB-TO-DIR: {<FVB><TO><DIR>+}  # 3

                VB-ITEM: {<VB><(ACT|OBJ|LOC)>+}  # 2
                ITEM-VB: {<(ACT|OBJ|LOC)>+<VB>}  # 2

                FVB-DIR-NUM: {<FVB><DIR><NUM>}  # 3
                DIR-NUM: {<DIR><NUM>}  # 2
                FVB-ALL: {<FVB><ALL>}  # take/drop/place/etc.. all 2
                FVB-ITEM: {<FVB><(OBJ|CONT)>+}  # take/drop/place/etc.. knife/backpack (multiple allowed) 2
                          {<FVB><DIR>+}  # goto north, south, etc.. (multiple allowed) 2
                          {<FVB><ACT>}  # attack troll, can only attack one thing at once. 2
                DIR: {<DIR>+}  # 1
                LVB: {<LVB>}  # 1
                BUILTIN-CMD: {<asf>}  # 1
                """

specific_errors = r"""
                  FVB-ERR: {<FVB><ERR>+}  # 2
                  FVB: {<FVB>}  # 1
                  OBJ/ACT: {<(OBJ|CONT|ACT)>}  # 1
                  """

partial_rearrangements = r"""
                        PFVB-OBJ/ALL-PFVB-OUT-FROM-IN-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<PFVB>+<OUT><FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}  # 8
                        PFVB-OBJ/ALL-PFVB-OUT-OF/FROM-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<PFVB>+<OUT><(OF|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 7
                        PFVB-OBJ/ALL-PFVB-IN/FROM-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<PFVB>+<(IN|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 6
                        PFVB-OBJ/ALL-PFVB-FROM-IN-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<PFVB>+<FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}

                        PFVB-OBJ/ALL-OUT-FROM-IN-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<OUT><FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}  # 8
                        PFVB-OBJ/ALL-OUT-OF/FROM-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<OUT><(OF|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 7
                        PFVB-OBJ/ALL-IN/FROM-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<(IN|FROM)><CONT><BUT>?<(OBJ|CONT)>?}  # 6
                        PFVB-OBJ/ALL-FROM-IN-CONT: {<PFVB>+(<(OBJ|CONT)>+|<ALL>)<FROM><IN><CONT><BUT>?<(OBJ|CONT)>?}

                        PFVB-ALL/ITEM-PFVB: {<PFVB>+(<(ACT|OBJ|LOC|CONT)>+|<ALL>)<PFVB>+}
                        PVB-ITEM-PVB: {<PVB>+<(ACT|OBJ|LOC)>+<PVB>+}
                        PFVB-ALL/ITEM: {<PFVB>+(<(ACT|OBJ|LOC|CONT)>+|<ALL>)}
                        PVB-ITEM: {<PVB>+<(ACT|OBJ|LOC)>+}
                        POBJ-ADJ: {<POBJ><ADJ>+}
                        ADJ-POBJ: {<ADJ>+<POBJ>}
                        USE-POBJ-TO-FVB-ACT/OBJ: {<USE><POBJ><TO><FVB><(ACT|OBJ)>}
                        """

# Constants
OBJ = 'OBJ'
WITH = 'WITH'
FVB = 'FVB'
ACT = 'ACT'
AND = 'AND'
DIR = 'DIR'
USE = 'USE'
TO = 'TO'
AT = 'AT'
IN = 'IN'
BUT = 'BUT'
ALL = 'ALL'
CONT = 'CONT'
