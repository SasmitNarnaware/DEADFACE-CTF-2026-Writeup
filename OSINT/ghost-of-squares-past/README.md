# Ghost of Squares Past — DEADFACE CTF 2026 Write-up

| | |
|---|---|
| **Category** | OSINT |
| **Points** | 150 |
| **Author** | @RP-01? |
| **Flag** | `deadface{1733-1742-1815-1733-gordon}` |

---

DEADFACE CTF: Ghost of Squares Past (OSINT) Write-up
Category: OSINT | Points: 150 | Author: @RP-01?

Challenge Overview
Intelligence indicates the DEADFACE threat group hid a coded message using Savannah, Georgia's historic squares. We are given five clues (a mix of riddles and missing images) that form a compass pattern: North, East, South, West, and Center.

Objective: Find the establishment years for the four outer squares (Points 1-4) and the surname engraved on the monument at the center square (Point 5).
Flag Format: deadface{YYYY-YYYY-YYYY-YYYY-surname}

Solution Walkthrough
To solve this, we must map out Savannah's historic district, anchor ourselves using the clear text riddles (Points 1 and 3), and use the compass pattern to deduce the remaining locations.

Step 1: Solving the Riddles (North and South)
We start with the two explicit text riddles provided in the prompt.

Point 1 (North)

"First of them all, where the city began, A banker's green heart in Oglethorpe's plan. A Quaker from Rhode Island sleeps under stone here..."

OSINT Data: A quick search for Savannah's first square reveals it is Johnson Square. It is known as the center of Savannah's financial district ("banker's green heart"). General Nathanael Greene, originally a Rhode Island Quaker, is buried under the monument there.

Establishment Year: 1733

Point 3 (South)

"battle of a northern frontier... eighteen-twelve... feather once drifted... founder stands tall... the newest of all"

OSINT Data: "Eighteen-twelve" and "northern frontier" point to the Battle of Chippawa. The drifting feather is a famous reference to the opening scene of Forrest Gump, which was filmed in Chippewa Square. The square also features a large statue of Georgia's founder, James Oglethorpe.

Establishment Year: 1815

Step 2: Deducing the Compass and Missing Locations
The prompt states the points form a compass pattern (1=North, 2=East, 3=South, 4=West) with the 5th point in the center. Even without the missing image files for Points 2 and 4, we can locate them using geography.

Looking at a map of Savannah's historic district, Johnson Square (North) and Chippewa Square (South) both sit perfectly aligned along Bull Street.

Point 5 (Center): The exact midpoint between Johnson and Chippewa on Bull Street is Wright Square.

Point 2 (East): The square sitting immediately East of Wright Square (along the intersecting President Street) is Oglethorpe Square.

Establishment Year: 1742

Point 4 (West): The square immediately West of Wright Square is Telfair Square (originally St. James Square).

Establishment Year: 1733

Step 3: Finding the Center Monument (Point 5)
"seek the lone name Carved in the stone where their center lays claim."

OSINT Data: We established the center is Wright Square. A search for monuments in Wright Square leads to the massive stone monument dedicated to William Washington Gordon, an early mayor and railroad pioneer.

While one side has a long plaque, looking at photos of the north-facing panel of the monument reveals a single word carved deeply into the stone: his surname.

Surname: gordon

Final Flag Construction
We assemble the findings in the requested order: Point 1 (1733) - Point 2 (1742) - Point 3 (1815) - Point 4 (1733) - Point 5 (gordon).

Flag: deadface{1733-1742-1815-1733-gordon}
