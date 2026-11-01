"""
The Royal Knot — Luxury Catering Menu Presets & Starter Templates

Provides three pre-engineered luxury palace banquet templates:
1. Royal Rajputana Mewari Feast (Traditional Marwari & Mewari Heritage Cuisine)
2. Mughal Sheesh Mahal Degustation (Awadhi Dum & Royal Mughal Banquet)
3. Contemporary Pan-Asian Luxury (Modern Fusion & Artisanal Asian Degustation)

These templates serve as editable starting blueprints for agency wedding planners.
Staff can customize, add, delete, and reorder courses and dishes before saving a catering plan.
"""

from typing import List, Dict, Any
import copy


LUXURY_MENU_PRESETS: Dict[str, Dict[str, Any]] = {
    "mewari_feast": {
        "id": "mewari_feast",
        "name": "Royal Rajputana Mewari Feast",
        "tagline": "Traditional Mewari Royalty & Lake Palace Banqueting",
        "description": (
            "Authentic Marwari and Mewari royal culinary heritage. Features live ghee counters, "
            "slow-roasted game specialties, smoked clay pot lentils, and gold-leaf desert confections."
        ),
        "recommended_service_style": "Silver Platter Degustation",
        "cuisine_preference": "Rajasthani Mewari Heritage",
        "items": [
            {
                "course_category": "Welcome Drinks",
                "item_name": "Kesar Kasturi Royal Elixir",
                "description": "Infused Kashmiri saffron, rose petals, crushed cardamom, and sparkling mineral water.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "1 glass per guest upon arrival",
                "display_order": 1,
            },
            {
                "course_category": "Welcome Drinks",
                "item_name": "Fresh Kokum & Mint Panna",
                "description": "Wild roasted cumin, mountain rock salt, fresh mint reduction.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Passed welcome beverage",
                "display_order": 2,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Smoked Khargosh & Shikar Kebab",
                "description": "Traditional royal hunting-style spiced mince skewered over charcoal embers.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Passed cocktail canapé",
                "display_order": 3,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Ker Sangri Tartlets with Fig Glaze",
                "description": "Desert beans and wild berries slow-simmered in cold-pressed mustard oil in savory filo pastry.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Passed cocktail canapé",
                "display_order": 4,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Paneer Ke Soley",
                "description": "House-crafted buffalo milk paneer rolls stuffed with spiced dried plums and mint chutney.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Plated appetizer",
                "display_order": 5,
            },
            {
                "course_category": "Live Artisanal Counters",
                "item_name": "Artisanal Bati & Ghee Tasting Bar",
                "description": "Stone-ground wheat batis with a tasting selection of A2 Bilona cow ghee, garlic chutney, and jaggery crumble.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Interactive live chef station",
                "display_order": 6,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Royal Mewari Laal Maas",
                "description": "Tender young mutton slow-cooked for 8 hours with Mathania red chilies, smoked clove, and pure ghee.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Served family-style in silver vessels",
                "display_order": 7,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Govind Gatta Curry",
                "description": "Steamed gram flour dumplings stuffed with mawa and pistachios in rich yogurt-fenugreek gravy.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Served family-style",
                "display_order": 8,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Jodhpuri Gattey & Mawa Pulao",
                "description": "Aged Dehraduni Basmati rice perfumed with saffron, caramelised onions, and toasted whole nuts.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Main starch",
                "display_order": 9,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Panchmel Dal Tadka",
                "description": "Five-lentil stew tempered with hing, cumin, dried chilies, and fresh coriander.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Continuous table service",
                "display_order": 10,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Bajra Roti & Khasta Missi Roti",
                "description": "Clay oven millet flatbreads brushed with homemade white butter.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Hot fresh from tandoor",
                "display_order": 11,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Kundan Kalakand with Silver Vark",
                "description": "Granular milk fudge with pistachio slivers and edible silver foil.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Banquet dessert station",
                "display_order": 12,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Jaleba & Malpua with Rabdi Glaze",
                "description": "Crisp giant saffron jalebi and reduced sweetened condensed milk.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Live dessert counter",
                "display_order": 13,
            },
        ],
    },
    "sheesh_mahal": {
        "id": "sheesh_mahal",
        "name": "Mughal Sheesh Mahal Degustation",
        "tagline": "Imperial Awadhi Nawabi & Sheesh Mahal Grandeur",
        "description": (
            "Imperial banqueting inspired by Mughal courtly traditions. Highlights include melt-in-mouth "
            "Kakori kebabs, slow-dum aromatic biryanis, gold-foiled curries, and rich cardamom phirnis."
        ),
        "recommended_service_style": "Royal Thali & Plated Service",
        "cuisine_preference": "Mughlai & Awadhi Nawabi",
        "items": [
            {
                "course_category": "Welcome Drinks",
                "item_name": "Shahi Rooh-e-Gulab Sharbat",
                "description": "Damask rose distillate with sweet basil seeds and silver pearls.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "1 welcome flute per guest",
                "display_order": 1,
            },
            {
                "course_category": "Welcome Drinks",
                "item_name": "Pistachio Almond Badam Harira",
                "description": "Warm spiced almond nectar perfumed with nutmeg and saffron.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Served in clay kulhads",
                "display_order": 2,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Smoked Truffle Galouti Kebab",
                "description": "Ultra-fine minced lamb patties smoked with cloves, served on mini saffron sheermal rounds.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Passed cocktail service",
                "display_order": 3,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Dahi Ke Kebab with Pomegranate Reduction",
                "description": "Hung yogurt cutlets stuffed with green chilies, coriander, and golden pine nuts.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Plated appetizer",
                "display_order": 4,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Bhatti Murgh Tikka",
                "description": "Char-grilled country chicken morsels marinated in yellow mustard, hung curd, and roasted garam masala.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Passed skewer",
                "display_order": 5,
            },
            {
                "course_category": "Live Artisanal Counters",
                "item_name": "Dum Biryani Handi Station",
                "description": "Clay handis sealed with dough, unsealed live before guests releasing fragrant cardamom steam.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Live carving station",
                "display_order": 6,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Awadhi Gosht Dum Biryani",
                "description": "Fragrant aged basmati rice cooked on dum with marinated baby lamb and saffron milk.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Main centerpiece",
                "display_order": 7,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Subz Nizami Handi Biryani",
                "description": "Seasonal baby vegetables and basmati layered with rose water and mint.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Vegetarian main course",
                "display_order": 8,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Murgh Badam Korma",
                "description": "Slow-braised chicken cooked in velvety white almond and cashew gravy.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Main course curry",
                "display_order": 9,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Paneer Kundan Qaliyan",
                "description": "Cottage cheese cubes bathed in yellow turmeric and saffron-scented gravy.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Vegetarian main course",
                "display_order": 10,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Dal Makhani Bukhara",
                "description": "Black lentils slow-cooked for 24 hours with butter and vine-ripened tomatoes.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Signature side",
                "display_order": 11,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Warqi Paratha & Taftan Breads",
                "description": "Flaky saffron-perfumed layered bread and sweet leavened bread.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Fresh oven basket",
                "display_order": 12,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Zafrani Phirni in Earthen Pots",
                "description": "Rice pudding infused with Kashmiri saffron, topped with edible 24K gold foil.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Individual earthenware bowls",
                "display_order": 13,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Shahi Tukda with Condensed Khoya Cream",
                "description": "Crisp fried brioche soaked in saffron cardamom syrup with rich malai.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Plated dessert",
                "display_order": 14,
            },
        ],
    },
    "pan_asian": {
        "id": "pan_asian",
        "name": "Contemporary Pan-Asian Luxury",
        "tagline": "Modern Starlit Luxury & Artisanal Asian Degustation",
        "description": (
            "Modern culinary concept tailored for glamorous Sangeet and cocktail evenings. Combines live "
            "dim sum steamers, robata charcoal grills, fresh truffle aromas, and contemporary pastry architecture."
        ),
        "recommended_service_style": "Multi-Cuisine Buffet & Live Stations",
        "cuisine_preference": "Contemporary Pan-Asian & Japanese Robata",
        "items": [
            {
                "course_category": "Welcome Drinks",
                "item_name": "Lychee Lemongrass Sparkling Spritzer",
                "description": "Thai lemongrass syrup, fresh lychee pearls, cold brew green tea, sparkling soda.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Welcome cocktail flute",
                "display_order": 1,
            },
            {
                "course_category": "Welcome Drinks",
                "item_name": "Yuzu Ginger Mocktail",
                "description": "Japanese yuzu extract, ginger reduction, butterfly pea flower tea layer.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Welcome beverage",
                "display_order": 2,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Truffle Edamame Crystal Dim Sum",
                "description": "Translucent dumplings filled with crushed edamame and black summer truffle oil.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Passed cocktail canapé",
                "display_order": 3,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Wild Prawn Har Gow with Tobiko",
                "description": "Steamed prawn dumpling with flying fish roe and scallion emulsion.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Passed cocktail canapé",
                "display_order": 4,
            },
            {
                "course_category": "Royal Appetizers & Starters",
                "item_name": "Avocado & Asparagus Uramaki Roll",
                "description": "Rolled vinegared rice with Hass avocado, grilled asparagus, and spicy vegan mayo.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Sushi bar selection",
                "display_order": 5,
            },
            {
                "course_category": "Live Artisanal Counters",
                "item_name": "Robata Charcoal Skewer Station",
                "description": "Live charcoal grill offering tender chicken yakitori, king oyster mushrooms, and glazed tofu.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Live interactive station",
                "display_order": 6,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Chilean Sea Bass in Mirin-Miso Glaze",
                "description": "Pan-seared sea bass marinated for 48 hours in white Saikyo miso, served with bok choy.",
                "dietary_tag": "Non-Vegetarian",
                "quantity_note": "Plated entrée",
                "display_order": 7,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Lotus Root & Water Chestnut in XO Chilli",
                "description": "Crunchy root vegetables wok-tossed in artisanal vegetarian XO sauce with roasted sesame.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Vegetarian main course",
                "display_order": 8,
            },
            {
                "course_category": "Main Degustation Courses",
                "item_name": "Silken Tofu & Shiitake Claypot",
                "description": "Braised Japanese mushrooms, tender tofu cubes, and bamboo shoots in garlic-soya broth.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Vegetarian main course",
                "display_order": 9,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Truffle Butter Garlic Fried Rice",
                "description": "Wok-fried Jasmine rice with crispy garlic flakes, scallions, and black truffle drizzle.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Signature starch",
                "display_order": 10,
            },
            {
                "course_category": "Breads & Dal",
                "item_name": "Hand-Pulled Dan Dan Noodles",
                "description": "Springy wheat noodles in spicy sesame peanut broth with crushed Sichuan peppers.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Live noodle counter",
                "display_order": 11,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Matcha Pistachio Opera Cake",
                "description": "Layers of Japanese green tea sponge, dark chocolate ganache, and pistachio buttercream.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Dessert atelier piece",
                "display_order": 12,
            },
            {
                "course_category": "Dessert Atelier",
                "item_name": "Black Sesame & Mango Mochi Ice Cream",
                "description": "Sweet rice dough enclosing artisanal tropical fruit and roasted sesame gelatos.",
                "dietary_tag": "Vegetarian",
                "quantity_note": "Passed dessert bite",
                "display_order": 13,
            },
        ],
    },
}


def get_available_presets() -> List[Dict[str, Any]]:
    """Returns metadata summary list for all luxury starting templates."""
    summaries = []
    for pid, pdata in LUXURY_MENU_PRESETS.items():
        summaries.append({
            "id": pdata["id"],
            "name": pdata["name"],
            "tagline": pdata["tagline"],
            "description": pdata["description"],
            "recommendedServiceStyle": pdata["recommended_service_style"],
            "cuisinePreference": pdata["cuisine_preference"],
            "totalItems": len(pdata["items"]),
            "coursesCount": len(set(i["course_category"] for i in pdata["items"])),
        })
    return summaries


def get_preset_by_id(preset_id: str) -> Dict[str, Any]:
    """Retrieves full preset details or raises ValueError if not found."""
    clean_id = (preset_id or "").strip().lower()
    if clean_id in ("pan_asian_luxury", "pan-asian-luxury", "panasian"):
        clean_id = "pan_asian"
    for pid, pdata in LUXURY_MENU_PRESETS.items():
        if pid == clean_id or pdata["name"].lower() == clean_id:
            return copy.deepcopy(pdata)
    valid = list(LUXURY_MENU_PRESETS.keys())
    raise ValueError(f"Preset '{preset_id}' not found. Available presets: {', '.join(valid)}")


def get_preset_items(preset_id: str) -> List[Dict[str, Any]]:
    """Returns a fresh deep-copy of course dishes from the specified template."""
    preset = get_preset_by_id(preset_id)
    return copy.deepcopy(preset["items"])

