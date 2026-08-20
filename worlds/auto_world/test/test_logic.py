from .bases import AutoWorldTestBase


class TestDefaultAutoWorld(AutoWorldTestBase):
    options = {
        "location_count": 20,
        "progression_tiers": 3,
        "goal": "victory_token",
    }

    def test_progression_logic(self):
        # Tier 1 should be accessible with no items
        self.assertTrue(self.can_reach_location("Tier 1 - Check 1"))
        # Tier 2 requires Tier 2 Key
        self.assertFalse(self.can_reach_location("Tier 2 - Check 1"))
        self.collect_by_name("Tier 2 Key")
        self.assertTrue(self.can_reach_location("Tier 2 - Check 1"))
        # Tier 3 requires Tier 3 Key
        self.assertFalse(self.can_reach_location("Tier 3 - Check 1"))
        self.collect_by_name("Tier 3 Key")
        self.assertTrue(self.can_reach_location("Tier 3 - Check 1"))

    def test_victory_condition(self):
        self.assertBeatable(False)
        self.collect_by_name("Victory Token")
        self.assertBeatable(True)


class TestFullClearGoal(AutoWorldTestBase):
    options = {
        "location_count": 15,
        "progression_tiers": 3,
        "goal": "full_clear",
    }

    def test_full_clear_goal(self):
        self.assertBeatable(False)
        self.collect_by_name("Tier 2 Key")
        self.assertBeatable(False)
        self.collect_by_name("Tier 3 Key")
        self.assertBeatable(True)


class TestLargeAutoWorld(AutoWorldTestBase):
    options = {
        "location_count": 300,
        "progression_tiers": 15,
        "goal": "victory_token",
    }

    def test_large_world_tiers(self):
        # Verify 300 locations generated
        locations = list(self.multiworld.get_locations(self.player))
        self.assertEqual(len(locations), 300)

        # Tier 1 check accessible with nothing
        self.assertTrue(self.can_reach_location("Tier 1 - Check 1"))

        # Tier 15 requires Tier 15 Key
        self.assertFalse(self.can_reach_location("Tier 15 - Check 1"))
        self.collect_by_name("Tier 15 Key")
        self.assertTrue(self.can_reach_location("Tier 15 - Check 1"))

    def test_large_world_victory(self):
        self.assertBeatable(False)
        self.collect_by_name("Victory Token")
        self.assertBeatable(True)
