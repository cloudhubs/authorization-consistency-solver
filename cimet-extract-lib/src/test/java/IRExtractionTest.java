import edu.university.ecs.lab.common.config.ConfigUtil;
import edu.university.ecs.lab.common.models.ir.Endpoint;
import edu.university.ecs.lab.common.models.ir.JClass;
import edu.university.ecs.lab.common.models.ir.MicroserviceSystem;
import edu.university.ecs.lab.common.models.ir.RestCall;
import edu.university.ecs.lab.common.services.GitService;
import edu.university.ecs.lab.common.utils.JsonReadWriteUtils;
import edu.university.ecs.lab.common.utils.SourceToObjectUtils;
import org.eclipse.jgit.api.errors.GitAPIException;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import edu.university.ecs.lab.intermediate.create.services.IRExtractionService;

import java.io.File;
import java.io.IOException;
import java.util.Optional;

public class IRExtractionTest {
    @Test
    void testGenerateIR() throws GitAPIException, IOException, InterruptedException {
        final String TEST_CONFIG_FILE = TestUtilities.CONFIGS_PATH + File.separator + "test_config2.json";
        IRExtractionService irServ = new IRExtractionService(TEST_CONFIG_FILE, Optional.of("a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd"));
        irServ.generateIR("output/IR.json");
        System.out.println("Generated IR at output/IR.json.");
    }
}
