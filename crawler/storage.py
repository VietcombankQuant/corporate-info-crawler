import sqlite3
from .common_types import Location


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self._create_tables()

    def new_location(self):
        pass

    def _create_tables(self):
        self._create_locations_table()

    def _create_locations_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS locations(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level int NOT NULL,
                level_name TEXT NOT NULL,
                url TEXT NOT NULL,
                parent_id TEXT,
                parent TEXT
            );
        """
        self.db.execute(query)
        self.db.commit()

    def new_location(self, location: Location):
        query = """
            INSERT INTO locations
            VALUES
            ($id, $name, $level, $level_name, $url, $parent_id, $parent);
        """
        params = {
            "id": location.id,
            "name": location.name,
            "level": location.level,
            "level_name": location.level_name,
            "parent_id": location.parent_id,
            "parent": location.parent,
            "url": location.url
        }

        self.db.execute(query, params)
        self.db.commit()

    def locations(self, level: int) -> list[Location]:
        query = """
            SELECT id, name, level, level_name, url, parent_id, parent 
            FROM locations
            WHERE level = $level;
        """
        params = {"level": level}
        cursor = self.db.cursor()
        cursor.execute(query, params)

        results = []
        for record in cursor:
            location = Location(
                id=record[0],
                name=record[1],
                level=record[2],
                level_name=record[3],
                url=record[4],
                parent_id=record[5],
                parent=record[6],
            )
            results.append(location)

        cursor.close()

        return results

    def __del__(self):
        self.db.close()
