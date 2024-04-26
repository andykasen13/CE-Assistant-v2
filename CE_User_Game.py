from typing import Literal
from CE_Objective import CE_Objective
from CE_User_Objective import CE_User_Objective
from CE_Game import CE_Game
import CE_API_Reader

class CE_User_Game():
    """A game that a user owns. This class extends the :class:`CE_Game` class."""
    def __init__(self,
                 ce_id : str,
                 user_primary_objectives : list[CE_User_Objective],
                 user_community_objectives : list[CE_User_Objective] = []):
        self._ce_id = ce_id
        self._user_primary_objectives = user_primary_objectives
        self._user_community_objectives = user_community_objectives

    # ----------- getters -----------
    
    def get_user_points(self) :
        """Returns the total number of points this user has in this game."""
        total_points = 0
        for objective in self._user_primary_objectives :
            total_points += objective.get_user_points()
        return total_points
    
    def get_ce_id(self) :
        """Returns the Challenge Enthusiast ID associated with this game."""
        return self._ce_id
    
    def get_user_primary_objectives(self) :
        """Returns the array of Primary :class:`CE_User_Objective`'s associated with this game."""
        return self._user_primary_objectives
    
    def get_user_community_objectives(self) :
        """Returns the array of Community :class:`CE_User_Objective`'s associated with this game."""
        return self._user_community_objectives
    
    # --------- setters -----------

    def add_user_objective(self, objective : CE_User_Objective) :
        """Adds a user objective to the object's user_objective's array."""
        if not objective.is_community() : self._user_primary_objectives.append(objective)
        elif objective.is_community() : self._user_community_objectives.append(objective)
        
    # ----------- other methods ------------

    def get_regular_game(self) -> CE_Game :
        """Returns the regular :class:`CE_Game` object associated with this game."""
        return CE_API_Reader.get_api_page_data("game", self.get_ce_id())
    
    def to_dict(self) :
        """Returns this game as a dictionary as used in the MongoDB database.
        Example:
        ```
        "1e866995-6fec-452e-81ba-1e8f8594f4ea" : {
            "Primary Objectives" : {
                "d1c48bd5-14cb-444e-9301-09574dfbe86a" : 20
            }
        }
        ```
        """
        objective_dict : list[dict] = []
        for objective in self.get_user_primary_objectives() :
            objective_dict.append(objective.to_dict())

        game_dict = {}

        if len(objective_dict) != 0 :
            game_dict['Primary Objectives'] = objective_dict

        return {self.get_ce_id() : game_dict}