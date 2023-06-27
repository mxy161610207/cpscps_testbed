package app;

import common.struct.info.ActorInfo;
import common.struct.info.SensorInfo;
import common.struct.SensorData;
import common.struct.State;
import common.struct.enumeration.SensorMode;
import org.apache.commons.lang3.ObjectUtils;
import org.junit.Test;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Map;

public class PlatformConnecterApp extends AbstractApp {
    @Override
    public void getMsg(String sensorName, SensorData value) {
        logger.info(String.format("[%s]: getMsg(channel, msg) -> %s, %s", appName, sensorName, value));
        // TODO
    }

    @Override
    public void configApp() {
        this.appName = "PlatformConnecterApp";
        this.appDescription = "FooBar";
    }

    private static final String sensorName = "RoboMasterEP";
    private static final String actuatorName = "RoboMasterEP";

    public static void main(String[] args) throws InterruptedException, IOException, ClassNotFoundException {
        PlatformConnecterApp app = new PlatformConnecterApp();
        AppRemoteConnector connector = AppRemoteConnector.getInstance();
        connector.connectPlatform("127.0.0.1", 9090);
        connector.registerApp(app);
        connector.checkConnected();

        Map<String, SensorInfo> supportedSensors = connector.getSupportedSensors();
        if (supportedSensors.containsKey(sensorName) && supportedSensors.get(sensorName).state == State.ON) {
            connector.registerSensor(sensorName, SensorMode.PASSIVE, 10);
        } else {
            throw new RuntimeException();
        }

        Map<String, ActorInfo> supportedActuators = connector.getSupportedActors();
        if (supportedActuators.containsKey(actuatorName) && supportedActuators.get(actuatorName).state == State.ON) {
            connector.registerActor(actuatorName);
            // connector.setActorCmd("RoboMasterEP", "xSpeed 5");
        } else {
            throw new RuntimeException();
        }

        ServerSocket appServer = new ServerSocket(18888);
        Socket clientSocket = appServer.accept();

        BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
        PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);

        while(true){
            String cmd = in.readLine();
            if (cmd != null && (cmd.startsWith("SAFE: "))) {
                connector.setActorCmd(actuatorName, cmd);
            }else if ("EXIT".equals(cmd)) {
                break;
            } else {
                throw new RuntimeException();
            }
        }

        appServer.close();
        connector.unregisterApp(app);
        connector.disConnectPlatform();
    }
}