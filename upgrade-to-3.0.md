## Upgrade to Fusion 3.0 from 2.4.x

These scripts require that the following Python libraries are already installed: kazoo, requests

Steps to upgrade from Fusion 2.4.x to 3.0

1. Download new version of Fusion
2. Extract it to a folder. Here we'll call it `fusion-new`, just as an example:

   ```
    mkdir fusion-new
    tar -C fusion-new --strip-components=1 -xf fusion-3.0.0.tar.gz
    ```

3. Set `FUSION_OLD_HOME` env variable to the old version of Fusion (2.x)

4. Set `FUSION_HOME` env variable to the new version of Fusion (3.0) 

    `export FUSION_HOME=fusion-new/3.0.0`

5. Copy data from older fusion instance to new fusion instance

   `cp -R $FUSION_OLD_HOME/data/*  $FUSION_HOME/data/`

6. Run the config upgrade step. This upgrades the customized properties in `$FUSION_OLD_HOME/conf/config.sh` to the new properties file in 3.0.0 (`$FUSION_HOME/conf/fusion.properties`)

    ```
    cd fusion-upgrade-scripts-interal/src
    python upgrade-to-3.0.py --upgrade config
    ```

    After running the step, please check the upgrade config in `$FUSION_HOME/conf/config.sh` and make sure all the modified properties in config.sh are reflected. Pay particular attention to the ZK connection strings if your existing Fusion installation connected to an external Zookeeper cluster.

    If you are running distributed fusion, this step would have to be performed on all the Fusion nodes.
    Alternately, if all the fusion nodes use the same configuration, you may just copy the new fusion.properties to all the other nodes.

   ---
   
   **NOTE**: If you are running external Solr or Zookeeper, then modify the `group.default` property in
    fusion.properties to reflect the services that should be started when `bin/fusion` script is executed. 
   
   ---

7. Start the Zookeeper server which will be used by the new Fusion installation. If you are using the Zookeeper bundled within Fusion, that would be: 

    ```
    cd $FUSION_HOME
    ./bin/zookeeper start
    ```

8. Run the upgrade script

    ```
    cd fusion-upgrade-scripts-internal/src
    python upgrade-to-3.0.py --upgrade zk
    ```

9. Run 3.0.0 fusion (all services defined in fusion.properties) and validate via Fusion UI
    ```
    cd $FUSION_HOME
    ./bin/fusion start
    ```

10. After running all the services, run this command to upgrade your custom banana dashboards that are saved in Solr collection 'system_banana'.

    ```
    cd fusion-upgrade-scripts-internal/src
    python upgrade-to-3.0.py --upgrade banana
    ```

## Upgrade to Fusion 3.0 from Fusion 1.2.3 or 2.1

1. Follow the upgrade from 1.2 to 2.4 https://doc.lucidworks.com/fusion/2.4/Installation_and_Configuration/Upgrading_Fusion/upgrade-1_2-to-2_4.html
2. Once upgraded to 2.4, follow the steps above to upgrade from 2.4 to 3.0
