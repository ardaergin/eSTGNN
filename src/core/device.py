from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import pandas as pd
from rdflib import URIRef, Namespace, Literal, RDF
import datetime

from .measurement import Measurement


@dataclass(slots=True)
class Device:
    uri: URIRef
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    device_type: Optional[str] = None
    room: Optional[URIRef] = None
    measurements: List[Measurement] = field(default_factory=list)
    properties: Set[URIRef] = field(default_factory=set)
    measurements_by_property: Dict[URIRef, List[Measurement]] = field(default_factory=dict)
    
    def add_measurement(self, measurement: Measurement) -> None:
        self.measurements.append(measurement)
        if measurement.property_type:
            self.properties.add(measurement.property_type)
            self.measurements_by_property.setdefault(measurement.property_type, []).append(measurement)

    def get_measurements_by_property(self, property_type: URIRef) -> List[Measurement]:
        """Get all measurements of a specific property type."""
        return [measurement for measurement in self.measurements 
                if measurement.property_type == property_type]
        
    def get_measurements_in_timeframe(self, 
                                      start_time: datetime.datetime, 
                                      end_time: datetime.datetime) -> List[Measurement]:
        """Get all measurements within a specific timeframe."""
        return [measurement for measurement in self.measurements 
                if start_time <= measurement.timestamp <= end_time]
                
    def to_dataframe(self) -> pd.DataFrame:
        """Convert measurements to a Pandas DataFrame."""
        data = []
        for measurement in self.measurements:
            row = {
                "measurement_uri": str(measurement.meas_uri),
                "timestamp": measurement.timestamp,
                "value": measurement.value,
                "device_uri": str(self.uri),
                "device_type": self.device_type,
                "room": str(self.room) if self.room else None,
            }
            
            if measurement.property_type:
                row["property_type"] = str(measurement.property_type)
            if measurement.unit:
                row["unit"] = str(measurement.unit)
                
            data.append(row)
            
        df = pd.DataFrame(data)
        if not df.empty:
            df.sort_values("timestamp", inplace=True)
        return df
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary format."""
        return {
            "uri": str(self.uri),
            "manufacturer": self.manufacturer,
            "model": self.model,
            "device_type": self.device_type,
            "room": str(self.room) if self.room else None,
            "measurement_count": len(self.measurements),
            "properties": [str(property) for property in self.properties]
        }

    def to_rdf_triples(self):
        """Yield RDF triples representing this device."""
        saref = Namespace("https://saref.etsi.org/core/")
        s4ener = Namespace("https://saref.etsi.org/saref4ener/")
        ic = Namespace("https://interconnectproject.eu/example/")
        s4bldg = Namespace("https://saref.etsi.org/saref4bldg/")
        
        # Define the device as a Device
        yield (self.uri, RDF.type, s4ener.Device)
        
        # Add device metadata
        if self.manufacturer:
            yield (self.uri, saref.hasManufacturer, Literal(self.manufacturer))
        if self.model:
            yield (self.uri, saref.hasModel, Literal(self.model))
        if self.device_type:
            yield (self.uri, ic.hasDeviceType, Literal(self.device_type))
        
        # Link to room if available
        if self.room:
            yield (self.uri, s4bldg.isContainedIn, self.room)
        
        # Link to measurements
        for measurement in self.measurements:
            yield (self.uri, saref.makesMeasurement, measurement.meas_uri)
    
    def __repr__(self):
        return (f"Device({self.uri}, "
                f"type={self.device_type}, "
                f"manufacturer={self.manufacturer}, "
                f"model={self.model}, "
                f"room={self.room}, "
                f"measurements={len(self.measurements)})")

    def __hash__(self):
        return hash(self.uri)
        
    def __eq__(self, other):
        """Check equality based on URI."""
        if isinstance(other, Device):
            return self.uri == other.uri
        return False
