package tech.followthemoney.model;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;

public class TemporalExtent {
    /*
     * TemporalExtent represents a temporal range for an entity type in the data model.
     * It defines a start and end time for the entity, which can be used in temporal
     * queries. The start and end times are defined as lists of property names, which
     * are expected to be of type "date".
     */
    private final Schema schema;
    private final List<String> start;
    private final List<String> end;

    public TemporalExtent(Schema schema, List<String> start, List<String> end) {
        this.schema = schema;
        this.start = start;
        this.end = end;
    }

    public List<Property> getStartProperties() {
        List<Property> properties = new ArrayList<>();
        for (String name : start) {
            properties.add(schema.getProperty(name));
        }
        return properties;
    }

    public List<Property> getEndProperties() {
        List<Property> properties = new ArrayList<>();
        for (String name : end) {
            properties.add(schema.getProperty(name));
        }
        return properties;
    }

    public static TemporalExtent fromJson(Schema schema, JsonNode node) {
        List<String> start = ModelHelper.getJsonStringArray(node, "start");
        List<String> end = ModelHelper.getJsonStringArray(node, "end");
        return new TemporalExtent(schema, start, end);
    }
}
