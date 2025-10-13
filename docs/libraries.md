# Other libraries and runtimes

While the production and processing of FtM data is usually done in [Python](python/index.md), there are also other supported languages bindings. These do not support the same data cleaning and normalisation functions as the Python version, but instead are meant to help applications like user interfaces or downstream 

## TypeScript / JavaScript

FtM includes full TypeScript bindings for reading schema metadata and entity data. The TypeScript library also includes a set of icons for most entity types. You can install FtM using npm like this:

```bash
npm install @opensanctions/followthemoney
```

For guidance on how to use the library, we recommend exploring the test cases located in the `js/test` folder of the FtM repository.

## Java / JVM

Platform bindings for the Java Virtual Machine are published as [`tech.followthemoney:followthemoney`](https://central.sonatype.com/artifact/tech.followthemoney/followthemoney). They can be used in all JVM languages (Java, Scala, Kotlin), and cover the schema metadata, and support for both value-based and statement-based entity data

Here's a sample configuration snippet for `pom.xml` dependency:

```xml
<dependency>
    <groupId>tech.followthemoney</groupId>
    <artifactId>followthemoney</artifactId>
    <version>{{ ftm_version }}</version>
</dependency>
```

A basic use of the library might involve reading FtM entities and reflecting on their properties using the model metadata:

```java
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
```

To learn more about the usage, [explore the Javadoc](https://javadoc.io/doc/tech.followthemoney/followthemoney) for this library. We recommend also exploring the test cases contained in the `java/src/test` folder of the FtM repository.

## ICIJ Java Bindings

An alternative binding for Java was developed by Bruno Thomas, a developer working at ICIJ. His library is published here: [https://github.com/ICIJ/ftm.java](https://github.com/ICIJ/ftm.java).

## Docker container

The Docker container is based off `ubuntu:latest`, and contains an install of the Python library (in `/opt/followthemoney`) with all dependencies. You can pull the [latest image](https://github.com/opensanctions/followthemoney/pkgs/container/followthemoney) from the GitHub registry:

```bash
docker pull ghcr.io/opensanctions/followthemoney:latest
docker run --rm -t -i ghcr.io/opensanctions/followthemoney:latest
```

While the container can be used directly for experimentation, its intended purpose is as a base layer for other projects that use a Docker deployment strategy.

