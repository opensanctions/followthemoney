package tech.followthemoney;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import tech.followthemoney.entity.ValueEntity;
import tech.followthemoney.exc.SchemaException;
import tech.followthemoney.model.Model;

public class FtMLibraryDemo {
    public static void main(String[] args) {
        String path = "entities.ftm.json";
        try {
            BufferedReader reader = new BufferedReader(new FileReader(path));
            Model model = Model.loadDefault();
            ObjectMapper mapper = new ObjectMapper();
            String line;
            while ((line = reader.readLine()) != null) {
                JsonNode node = mapper.readTree(line);
                ValueEntity entity = ValueEntity.fromJson(model, node);
                System.out.println("Processing entity: " + entity.getId());
                System.out.println(" -> Entity name: " + entity.getCaption());
                System.out.println(" -> Entity type: " + entity.getSchema().getLabel());
            }
            
        } catch (IOException | SchemaException e) {
            e.printStackTrace();
        } 
    }
}
