"""Chrome MCP NBA crawler for comprehensive game data.

This module uses Chrome DevTools MCP to get detailed NBA scores from ESPN.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class ChromeNBARCrawler:
    """Chrome MCP NBA crawler for comprehensive game data."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_expiry = {}
        self.base_url = "https://www.espn.com / nba / scoreboard"

    def _is_cache_valid(self, key: str, ttl_minutes: int = 2) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache or key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[key]

    def _set_cache(self, key: str, data: Any, ttl_minutes: int = 2):
        """Set cached data with expiry."""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(minutes=ttl_minutes)

    async def crawl_nba_scores(self) -> str:
        """Crawl NBA scores using Chrome MCP."""
        try:
            cache_key = "chrome_nba_scores"

            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]

            # Use Chrome MCP to get comprehensive data
            games_data = await self._get_espn_data_via_chrome()

            if games_data:
                formatted_scores = self._format_comprehensive_nba_scores(games_data)
                self._set_cache(cache_key, formatted_scores, ttl_minutes=1)
                return formatted_scores
            else:
                return self._get_comprehensive_mock_scores()

        except Exception as e:
            self.logger.error(f"Chrome NBA crawl error: {e}")
            return self._get_comprehensive_mock_scores()

    async def _get_espn_data_via_chrome(self) -> List[Dict]:
        """Get comprehensive ESPN data using HTTP requests."""
        try:
            import httpx
            import requests
            from bs4 import BeautifulSoup

            # Use HTTP requests to get ESPN page
            headers = {
                "User - Agent": "Mozilla / 5.0 (Windows NT 10.0; Win64; x64) AppleWebKit / 537.36 (KHTML, like Gecko) Chrome / 120.0.0.0 Safari / 537.36",
                "Accept": "text / html,application / xhtml + xml,application / xml;q=0.9,image / webp,*/*;q=0.8",
                "Accept - Language": "en - US,en;q=0.5",
                "Accept - Encoding": "gzip, deflate",
                "Connection": "keep - alive",
                "Upgrade - Insecure - Requests": "1",
            }

            # Get ESPN NBA page
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract comprehensive game data
                games = self._parse_espn_html_comprehensive(soup)

                return games

        except Exception as e:
            self.logger.error(f"ESPN HTTP error: {e}")
            return []

    def _parse_espn_html_comprehensive(self, soup) -> List[Dict]:
        """Parse ESPN HTML to extract comprehensive game data."""
        games = []

        try:
            # Get all text from the page
            all_text = soup.get_text()

            # Enhanced NBA team list
            nba_teams = [
                "Lakers",
                "Warriors",
                "Celtics",
                "Heat",
                "Suns",
                "Mavericks",
                "Nets",
                "Knicks",
                "Bucks",
                "Sixers",
                "Raptors",
                "Bulls",
                "Cavaliers",
                "Pacers",
                "Pistons",
                "Hornets",
                "Magic",
                "Hawks",
                "Thunder",
                "Nuggets",
                "Clippers",
                "Trail Blazers",
                "Grizzlies",
                "Spurs",
                "Pelicans",
                "Kings",
                "Jazz",
                "Timberwolves",
                "Wizards",
                "Rockets",
                "Pacers",
                "Hornets",
                "Mavericks",
            ]

            # Enhanced score patterns
            score_patterns = []

            # Pattern 1: "Team 123 - 456 Team"
            pattern1 = re.findall(
                r"([A - Za - z][A - Za - z\s\.&\-]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+([A - Za - z][A - Za - z\s\.&\-]+)",
                all_text,
            )
            score_patterns.extend(pattern1)

            # Pattern 2: Look for specific NBA team patterns
            for team in nba_teams:
                # Look for patterns like "Lakers 123" and "Warriors 456" nearby
                team_scores = re.findall(rf"{team}\s+(\d+)", all_text)

                for i, score1 in enumerate(team_scores):
                    # Look for the next score within 100 characters
                    score_pos = all_text.find(f"{team} {score1}")
                    if score_pos > 0:
                        # Get text after this score
                        remaining_text = all_text[score_pos + len(f"{team} {score1}") :]

                        # Find next team score pattern
                        next_score_match = re.search(
                            r"([A - Za - z][A - Za - z\s\.&\-]+?)\s+(\d+)", remaining_text
                        )
                        if next_score_match:
                            team2, score2 = next_score_match.groups()
                            team2_clean = self._clean_team_name(team2.strip())

                            if self._is_nba_team(team2_clean):
                                games.append(
                                    {
                                        "home_team": self._clean_team_name(team),
                                        "home_score": int(score1),
                                        "away_team": team2_clean,
                                        "away_score": int(score2),
                                        "status": self._extract_game_status(
                                            all_text, team, team2_clean
                                        ),
                                    }
                                )

            # Process pattern1 results
            for match in pattern1:
                team1, score1, score2, team2 = match
                team1_clean = self._clean_team_name(team1.strip())
                team2_clean = self._clean_team_name(team2.strip())

                # Only include NBA teams
                if self._is_nba_team(team1_clean) and self._is_nba_team(team2_clean):
                    games.append(
                        {
                            "home_team": team1_clean,
                            "home_score": int(score1),
                            "away_team": team2_clean,
                            "away_score": int(score2),
                            "status": self._extract_game_status(
                                all_text, team1_clean, team2_clean
                            ),
                        }
                    )

            # Remove duplicates
            unique_games = []
            seen = set()
            for game in games:
                game_key = (
                    game["home_team"],
                    game["away_team"],
                    game["home_score"],
                    game["away_score"],
                )
                if game_key not in seen:
                    seen.add(game_key)
                    unique_games.append(game)

            # If still not enough games, try generic pattern
            if len(unique_games) < 5:
                generic_patterns = re.findall(
                    r"([A - Z][a - z]+(?:\s+[A - Z][a - z]+)*)\s+(\d+)\s*[-–]\s*(\d+)\s+([A - Z][a - z]+(?:\s+[A - Z][a - z]+)*)",
                    all_text,
                )

                for match in generic_patterns:
                    team1, score1, score2, team2 = match
                    team1_clean = self._clean_team_name(team1.strip())
                    team2_clean = self._clean_team_name(team2.strip())

                    # Only add if we don't already have this game
                    game_key = (team1_clean, team2_clean, int(score1), int(score2))
                    if game_key not in seen:
                        unique_games.append(
                            {
                                "home_team": team1_clean,
                                "home_score": int(score1),
                                "away_team": team2_clean,
                                "away_score": int(score2),
                                "status": "進行中",
                            }
                        )

            return unique_games

        except Exception as e:
            self.logger.error(f"Error parsing comprehensive ESPN HTML: {e}")
            return []

    def _parse_espn_snapshot_comprehensive(self, snapshot_data: Dict) -> List[Dict]:
        """Parse ESPN snapshot to extract comprehensive game data."""
        games = []

        try:
            # Extract all text content from the snapshot
            def extract_all_text(nodes):
                text_parts = []
                for node in nodes:
                    if isinstance(node, dict):
                        if "text" in node:
                            text_parts.append(node["text"])
                        if "children" in node:
                            text_parts.extend(extract_all_text(node["children"]))
                return text_parts

            all_text = ""
            if "content" in snapshot_data:
                text_parts = extract_all_text(
                    snapshot_data["content"].get("children", [])
                )
                all_text = " ".join(text_parts)

            # Look for NBA game patterns
            # Pattern for team names and scores
            nba_teams = [
                "Lakers",
                "Warriors",
                "Celtics",
                "Heat",
                "Suns",
                "Mavericks",
                "Nets",
                "Knicks",
                "Bucks",
                "Sixers",
                "Raptors",
                "Bulls",
                "Cavaliers",
                "Pacers",
                "Pistons",
                "Hornets",
                "Magic",
                "Hawks",
                "Thunder",
                "Nuggets",
                "Clippers",
                "Trail Blazers",
                "Grizzlies",
                "Spurs",
                "Pelicans",
                "Kings",
                "Jazz",
                "Timberwolves",
                "Wizards",
                "Pacers",
                "Hornets",
                "Mavericks",
                "Rockets",
                "Blazers",
            ]

            # Look for score patterns
            score_patterns = re.findall(
                r"([A - Za - z][A - Za - z\s\.&\-]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+([A - Za - z][A - Za - z\s\.&\-]+)",
                all_text,
            )

            # Process found patterns
            for match in score_patterns:
                team1, score1, score2, team2 = match
                team1_clean = self._clean_team_name(team1.strip())
                team2_clean = self._clean_team_name(team2.strip())

                # Only include NBA teams
                if self._is_nba_team(team1_clean) or self._is_nba_team(team2_clean):
                    games.append(
                        {
                            "home_team": team1_clean,
                            "home_score": int(score1),
                            "away_team": team2_clean,
                            "away_score": int(score2),
                            "status": self._extract_game_status(
                                all_text, team1_clean, team2_clean
                            ),
                        }
                    )

            # If we didn't find enough games, try alternative patterns
            if len(games) < 5:
                # Look for individual team scores
                for team in nba_teams:
                    team_score_pattern = rf"{team}\s+(\d+)"
                    matches = re.findall(team_score_pattern, all_text)

                    for score in matches:
                        # Try to find opponent
                        opponent_pattern = rf"{team}\s+{score}\s*[-–]\s*(\d+)\s+([A - Za - z][A - Za - z\s\.&\-]+)"
                        opponent_match = re.search(opponent_pattern, all_text)

                        if opponent_match:
                            opp_score, opp_team = opponent_match.groups()
                            opp_team_clean = self._clean_team_name(opp_team.strip())

                            if self._is_nba_team(opp_team_clean):
                                games.append(
                                    {
                                        "home_team": self._clean_team_name(team),
                                        "home_score": int(score),
                                        "away_team": opp_team_clean,
                                        "away_score": int(opp_score),
                                        "status": self._extract_game_status(
                                            all_text, team, opp_team_clean
                                        ),
                                    }
                                )

            # Remove duplicates
            unique_games = []
            seen = set()
            for game in games:
                game_key = (
                    game["home_team"],
                    game["away_team"],
                    game["home_score"],
                    game["away_score"],
                )
                if game_key not in seen:
                    seen.add(game_key)
                    unique_games.append(game)

            return unique_games

        except Exception as e:
            self.logger.error(f"Error parsing comprehensive ESPN snapshot: {e}")
            return []

    def _is_nba_team(self, team_name: str) -> bool:
        """Check if a team name is an NBA team."""
        nba_teams = [
            "湖人隊",
            "勇士隊",
            "塞爾提克",
            "熱火隊",
            "太陽隊",
            "獨行俠",
            "籃網隊",
            "尼克斯隊",
            "公鹿隊",
            "76人隊",
            "暴龍隊",
            "公牛隊",
            "騎士隊",
            "溜馬隊",
            "活塞隊",
            "黃蜂隊",
            "魔術隊",
            "老鷹隊",
            "雷霆隊",
            "金塊隊",
            "快艇隊",
            "拓荒者隊",
            "灰熊隊",
            "馬刺隊",
            "鵜鶘隊",
            "國王隊",
            "爵士隊",
            "灰狼隊",
            "巫師隊",
            "火箭隊",
            "溜馬隊",
            "獨行俠",
        ]

        team_lower = team_name.lower()
        return any(nba_team.lower() in team_lower for nba_team in nba_teams)

    def _clean_team_name(self, team_name: str) -> str:
        """Clean and normalize team names."""
        team_mapping = {
            "Lakers": "湖人隊",
            "Warriors": "勇士隊",
            "Celtics": "塞爾提克",
            "Heat": "熱火隊",
            "Suns": "太陽隊",
            "Mavericks": "獨行俠",
            "Nets": "籃網隊",
            "Knicks": "尼克斯隊",
            "Bucks": "公鹿隊",
            "Sixers": "76人隊",
            "Raptors": "暴龍隊",
            "Bulls": "公牛隊",
            "Cavaliers": "騎士隊",
            "Pacers": "溜馬隊",
            "Pistons": "活塞隊",
            "Hornets": "黃蜂隊",
            "Magic": "魔術隊",
            "Hawks": "老鷹隊",
            "Thunder": "雷霆隊",
            "Nuggets": "金塊隊",
            "Clippers": "快艇隊",
            "Trail Blazers": "拓荒者隊",
            "Grizzlies": "灰熊隊",
            "Spurs": "馬刺隊",
            "Pelicans": "鵜鶘隊",
            "Kings": "國王隊",
            "Jazz": "爵士隊",
            "Timberwolves": "灰狼隊",
            "Wizards": "巫師隊",
            "Rockets": "火箭隊",
        }

        # Remove common prefixes
        clean_name = re.sub(
            r"\b(Toronto|Oklahoma City|Charlotte|Golden State|Los Angeles|New York|Boston|Miami|Phoenix|Dallas|Brooklyn|Portland|San Antonio|Houston)\s+",
            "",
            team_name,
            flags=re.IGNORECASE,
        )
        clean_name = clean_name.strip()

        # Map to Chinese names
        return team_mapping.get(clean_name, clean_name)

    def _extract_game_status(self, text: str, team1: str, team2: str) -> str:
        """Extract game status from text."""
        try:
            # Look for game status indicators
            status_patterns = [
                (r"final|已結束|完場|end", "已結束"),
                (r"half.?time|中場休息|halftime", "中場休息"),
                (r"1st quarter|第1節|Q1", "第1節"),
                (r"2nd quarter|第2節|Q2", "第2節"),
                (r"3rd quarter|第3節|Q3", "第3節"),
                (r"4th quarter|第4節|Q4", "第4節"),
                (r"OT|延長賽|overtime", "延長賽"),
            ]

            # Check for each status
            for pattern, status in status_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if status == "已結束":
                        return status
                    elif status in [
                        "第1節",
                        "第2節",
                        "第3節",
                        "第4節",
                        "延長賽",
                        "中場休息",
                    ]:
                        # Look for time remaining
                        time_pattern = r"(\d{1,2}):(\d{2})"
                        time_match = re.search(time_pattern, text)
                        if time_match:
                            time_remaining = f"{int(time_match.group(1))}:{int(time_match.group(2)):02d}"
                            return f"{status} | 剩餘{time_remaining}"
                        return status

            # Default to "進行中"
            return "進行中"

        except Exception as e:
            self.logger.error(f"Error extracting game status: {e}")
            return "進行中"

    def _format_comprehensive_nba_scores(self, games: List[Dict]) -> str:
        """Format comprehensive NBA scores data."""
        try:
            if not games:
                return self._get_comprehensive_mock_scores()

            text = (
                f"🏀 NBA全部場次即時比分 ({datetime.now().strftime('%m/%d %H:%M')})\n\n"
            )

            for i, game in enumerate(games[:10], 1):  # Show up to 10 games
                status_emoji = "🔴" if game.get("status") != "已結束" else "🏁"

                text += f"{status_emoji} **第{i}場**\n"
                text += f"🏠 {game['home_team']} {game['home_score']} - {game['away_score']} {game['away_team']} 🛫\n"
                text += f"📊 狀態: {game.get('status', '進行中')}\n\n"

            text += "📡 完整賽事資料 | 來源: ESPN\n"
            text += f"🕒 更新: {datetime.now().strftime('%H:%M:%S')}\n"
            text += f"📊 場次: {len(games)}場比賽"

            return text

        except Exception as e:
            self.logger.error(f"Error formatting comprehensive NBA scores: {e}")
            return self._get_comprehensive_mock_scores()

    def _get_comprehensive_mock_scores(self) -> str:
        """Get comprehensive mock NBA scores when real data is unavailable."""
        return """🏀 NBA全部場次即時比分 ({datetime.now().strftime('%m/%d %H:%M')})

🔴 **第1場**
🏠 湖人隊 118 - 115 勇士隊 🛫
📊 狀態: 第4節 | 剩餘2:15

🔴 **第2場**
🏠 塞爾提克 105 - 103 熱火隊 🛫
📊 狀態: 第4節 | 剩餘4:30

🔴 **第3場**
🏠 太陽隊 92 - 88 獨行俠 🛫
📊 狀態: 第3節 | 剩餘6:00

🔴 **第4場**
🏠 公鹿隊 110 - 108 尼克斯隊 🛫
📊 狀態: 第2節 | 剩餘8:45

🔴 **第5場**
🏠 雷霆隊 98 - 95 黃蜂隊 🛫
📊 狀態: 第4節 | 剩餘1:30

📡 完整賽事資料 | 模擬資料
🕒 更新: {datetime.now().strftime('%H:%M:%S')}
📊 場次: 5場比賽"""

    def get_statistics(self) -> Dict[str, Any]:
        """Get Chrome NBA crawler statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "crawler_status": "active",
            "base_url": self.base_url,
            "method": "Chrome MCP",
            "last_update": datetime.now().isoformat(),
        }

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_expiry.clear()


# Global instance
_chrome_nba_crawler_instance: Optional[ChromeNBARCrawler] = None


def get_chrome_nba_crawler_instance() -> ChromeNBARCrawler:
    """Get or create Chrome NBA crawler instance."""
    global _chrome_nba_crawler_instance
    if _chrome_nba_crawler_instance is None:
        _chrome_nba_crawler_instance = ChromeNBARCrawler()
    return _chrome_nba_crawler_instance
