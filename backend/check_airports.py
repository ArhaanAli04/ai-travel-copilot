"""
Check airports.json file
"""
import json
from pathlib import Path


def check_airports_json():
    print("\n" + "="*60)
    print("CHECKING AIRPORTS.JSON FILE")
    print("="*60)
    
    # Check file exists
    airports_file = Path(__file__).parent / "app" / "data" / "airports.json"
    print(f"\n📁 Looking for file at: {airports_file}")
    print(f"   File exists: {airports_file.exists()}")
    
    if not airports_file.exists():
        print("\n❌ ERROR: airports.json not found!")
        return
    
    # Check file size
    file_size = airports_file.stat().st_size
    print(f"   File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    # Load JSON
    try:
        print("\n📖 Loading JSON...")
        with open(airports_file, 'r', encoding='utf-8') as f:
            airports = json.load(f)
        
        print(f"✅ JSON loaded successfully!")
        print(f"   Type: {type(airports)}")
        print(f"   Total entries: {len(airports)}")
        
        # Show first airport
        if airports:
            first_key = list(airports.keys())[0]
            first_airport = airports[first_key]
            print(f"\n📍 First airport (key: {first_key}):")
            print(f"   {json.dumps(first_airport, indent=2)}")
        
        # Count airports with IATA codes
        print(f"\n🔍 Analyzing IATA codes...")
        airports_with_iata = {k: v for k, v in airports.items() if v.get('iata') and v.get('iata') != ''}
        print(f"   Airports with IATA codes: {len(airports_with_iata)}")
        print(f"   Airports without IATA: {len(airports) - len(airports_with_iata)}")
        
        # Show sample IATA codes
        sample_iata = list(airports_with_iata.values())[:10]
        sample_codes = [a.get('iata') for a in sample_iata]
        print(f"   Sample IATA codes: {sample_codes}")
        
        # Search for JFK
        print(f"\n🔍 Searching for JFK...")
        
        # Method 1: Search by IATA code
        jfk_by_iata = [v for k, v in airports.items() if v.get('iata') == 'JFK']
        if jfk_by_iata:
            print(f"✅ Found JFK by IATA:")
            print(f"   {json.dumps(jfk_by_iata[0], indent=2)}")
        else:
            print(f"❌ JFK not found by IATA code")
        
        # Method 2: Search by name containing "Kennedy"
        jfk_by_name = [v for k, v in airports.items() if 'Kennedy' in v.get('name', '')]
        if jfk_by_name:
            print(f"\n✅ Found airports with 'Kennedy' in name:")
            for apt in jfk_by_name[:3]:
                print(f"   - {apt.get('name')} (IATA: {apt.get('iata')}, ICAO: {apt.get('icao')})")
        
        # Search for other major airports
        print(f"\n🔍 Searching for other major airports...")
        test_codes = ['LAX', 'LHR', 'BOM', 'DEL', 'DXB']
        
        for code in test_codes:
            found = [v for k, v in airports.items() if v.get('iata') == code]
            if found:
                apt = found[0]
                print(f"   ✅ {code}: {apt.get('name')} (lat: {apt.get('lat')}, lon: {apt.get('lon')})")
            else:
                print(f"   ❌ {code}: Not found")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    check_airports_json()
