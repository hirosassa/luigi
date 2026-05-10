"""Tests that contrib modules raise clear ImportError when dependencies are missing."""

import builtins
import importlib
import sys
import unittest
from contextlib import contextmanager


@contextmanager
def hide_modules(*prefixes):
    """指定したプレフィックスのモジュールをsys.modulesから一時的に隠し、importを失敗させる。"""
    hidden = {}
    original_import = builtins.__import__

    # 既にロード済みのモジュールを退避
    for key in list(sys.modules):
        if any(key == p or key.startswith(p + ".") for p in prefixes):
            hidden[key] = sys.modules.pop(key)

    def mock_import(name, *args, **kwargs):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = mock_import
    try:
        yield
    finally:
        builtins.__import__ = original_import
        sys.modules.update(hidden)


def reload_without_deps(module_path, *dep_prefixes):
    """依存パッケージを隠した状態でモジュールをリロードして返す。"""
    # 対象モジュール自体もリロード対象にするため退避
    saved = sys.modules.pop(module_path, None)
    try:
        with hide_modules(*dep_prefixes):
            mod = importlib.import_module(module_path)
            importlib.reload(mod)
            return mod
    finally:
        # テスト後に元のモジュールを復元
        if saved is not None:
            sys.modules[module_path] = saved
            importlib.reload(saved)


class TestS3MissingDependency(unittest.TestCase):
    def test_s3client_raises_import_error_without_boto3(self):
        s3 = reload_without_deps("luigi.contrib.s3", "boto3", "botocore")
        with self.assertRaises(ImportError) as cm:
            s3.S3Client()
        self.assertIn("boto3", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestGCSMissingDependency(unittest.TestCase):
    def test_gcsclient_raises_import_error_without_googleapiclient(self):
        gcs = reload_without_deps("luigi.contrib.gcs", "googleapiclient", "httplib2", "google")
        with self.assertRaises(ImportError) as cm:
            gcs.GCSClient()
        self.assertIn("google-api-python-client", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))

    def test_gcstarget_raises_import_error_without_googleapiclient(self):
        gcs = reload_without_deps("luigi.contrib.gcs", "googleapiclient", "httplib2", "google")
        with self.assertRaises(ImportError) as cm:
            gcs.GCSTarget("/some/path")
        self.assertIn("google-api-python-client", str(cm.exception))

    def test_gcsflagtarget_raises_import_error_without_googleapiclient(self):
        gcs = reload_without_deps("luigi.contrib.gcs", "googleapiclient", "httplib2", "google")
        with self.assertRaises(ImportError) as cm:
            gcs.GCSFlagTarget("/some/path/")
        self.assertIn("google-api-python-client", str(cm.exception))


class TestBigQueryMissingDependency(unittest.TestCase):
    def test_bigqueryclient_raises_import_error(self):
        bq = reload_without_deps("luigi.contrib.bigquery", "googleapiclient", "httplib2", "google")
        with self.assertRaises(ImportError) as cm:
            bq.BigQueryClient()
        self.assertIn("google-api-python-client", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))

    def test_bigquerytarget_raises_import_error(self):
        bq = reload_without_deps("luigi.contrib.bigquery", "googleapiclient", "httplib2", "google")
        with self.assertRaises(ImportError) as cm:
            bq.BigQueryTarget("project", "dataset", "table")
        self.assertIn("google-api-python-client", str(cm.exception))


class TestDockerMissingDependency(unittest.TestCase):
    def test_dockertask_raises_import_error_without_docker(self):
        docker_runner = reload_without_deps("luigi.contrib.docker_runner", "docker")
        with self.assertRaises(ImportError) as cm:
            docker_runner.DockerTask()
        self.assertIn("docker", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestECSMissingDependency(unittest.TestCase):
    def test_ecstask_raises_import_error_without_boto3(self):
        ecs = reload_without_deps("luigi.contrib.ecs", "boto3", "botocore")
        with self.assertRaises(ImportError) as cm:
            ecs.ECSTask()
        self.assertIn("boto3", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestBatchMissingDependency(unittest.TestCase):
    def test_batchclient_raises_import_error_without_boto3(self):
        batch = reload_without_deps("luigi.contrib.batch", "boto3", "botocore")
        with self.assertRaises(ImportError) as cm:
            batch.BatchClient()
        self.assertIn("boto3", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))

    def test_batchtask_raises_import_error_without_boto3(self):
        batch = reload_without_deps("luigi.contrib.batch", "boto3", "botocore")
        with self.assertRaises(ImportError) as cm:
            batch.BatchTask(job_definition="test")
        self.assertIn("boto3", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestPostgresMissingDependency(unittest.TestCase):
    def test_postgrestarget_connect_raises_import_error_without_dbapi(self):
        pg = reload_without_deps("luigi.contrib.postgres", "psycopg2", "pg8000")
        target = pg.PostgresTarget("host", "db", "user", "pass", "table", "update_id")
        with self.assertRaises(ImportError) as cm:
            target.connect()
        self.assertIn("psycopg2", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestRedisMissingDependency(unittest.TestCase):
    def test_redistarget_raises_import_error_without_redis(self):
        redis_store = reload_without_deps("luigi.contrib.redis_store", "redis")
        with self.assertRaises(ImportError) as cm:
            redis_store.RedisTarget("host", 6379, 0, "update_id")
        self.assertIn("redis", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestSalesforceMissingDependency(unittest.TestCase):
    def test_salesforceapi_raises_import_error_without_requests(self):
        sf = reload_without_deps("luigi.contrib.salesforce", "requests")
        with self.assertRaises(ImportError) as cm:
            sf.SalesforceAPI("user", "pass", "token")
        self.assertIn("requests", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestDropboxMissingDependency(unittest.TestCase):
    def test_dropboxclient_raises_import_error_without_dropbox(self):
        dbx = reload_without_deps("luigi.contrib.dropbox", "dropbox")
        with self.assertRaises(ImportError) as cm:
            dbx.DropboxClient("token")
        self.assertIn("dropbox", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))

    def test_dropboxtarget_raises_import_error_without_dropbox(self):
        dbx = reload_without_deps("luigi.contrib.dropbox", "dropbox")
        with self.assertRaises(ImportError) as cm:
            dbx.DropboxTarget("/path", "token")
        self.assertIn("dropbox", str(cm.exception))


class TestEsindexMissingDependency(unittest.TestCase):
    def test_elasticsearchtarget_raises_import_error(self):
        es = reload_without_deps("luigi.contrib.esindex", "elasticsearch")
        with self.assertRaises(ImportError) as cm:
            es.ElasticsearchTarget("host", 9200, "index", "doc_type", "update_id")
        self.assertIn("elasticsearch", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestKubernetesMissingDependency(unittest.TestCase):
    def test_kubernetesjob_raises_import_error_without_pykube(self):
        k8s = reload_without_deps("luigi.contrib.kubernetes", "pykube")
        with self.assertRaises(ImportError) as cm:
            k8s.KubernetesJobTask()
        self.assertIn("pykube", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestMysqlMissingDependency(unittest.TestCase):
    def test_mysqltarget_raises_import_error(self):
        mysql = reload_without_deps("luigi.contrib.mysqldb", "mysql")
        with self.assertRaises(ImportError) as cm:
            mysql.MySqlTarget("host", "db", "user", "pass", "table", "update_id")
        self.assertIn("mysql-connector-python", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestMssqlMissingDependency(unittest.TestCase):
    def test_mssqltarget_raises_import_error(self):
        mssql = reload_without_deps("luigi.contrib.mssqldb", "pymssql")
        with self.assertRaises(ImportError) as cm:
            mssql.MSSqlTarget("host", "db", "user", "pass", "table", "update_id")
        self.assertIn("pymssql", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestPrestoMissingDependency(unittest.TestCase):
    def test_prestoclient_raises_import_error(self):
        presto = reload_without_deps("luigi.contrib.presto", "pyhive")
        with self.assertRaises(ImportError) as cm:
            presto.PrestoClient(None)
        self.assertIn("pyhive", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestDatadogMissingDependency(unittest.TestCase):
    def test_datadogmetricscollector_raises_import_error(self):
        dd = reload_without_deps("luigi.contrib.datadog_metric", "datadog")
        with self.assertRaises(ImportError) as cm:
            dd.DatadogMetricsCollector()
        self.assertIn("datadog", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestPaiMissingDependency(unittest.TestCase):
    def test_paitask_raises_import_error_without_requests(self):
        pai = reload_without_deps("luigi.contrib.pai", "requests")

        class ConcretePaiTask(pai.PaiTask):
            name = "test"
            image = "test"
            tasks = []

        with self.assertRaises(ImportError) as cm:
            ConcretePaiTask()
        self.assertIn("requests", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestBigQueryAvroMissingDependency(unittest.TestCase):
    def test_bigqueryloadavro_raises_import_error_without_avro(self):
        bqa = reload_without_deps("luigi.contrib.bigquery_avro", "avro")
        with self.assertRaises(ImportError) as cm:
            bqa.BigQueryLoadAvro()
        self.assertIn("avro", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestDataprocMissingDependency(unittest.TestCase):
    def test_dataprocbasetask_raises_import_error(self):
        dp = reload_without_deps("luigi.contrib.dataproc", "googleapiclient", "google")
        with self.assertRaises(ImportError) as cm:
            dp.DataprocSparkTask(gcloud_project_id="test", dataproc_cluster_name="test", main_class="com.example.Main")
        self.assertIn("google-api-python-client", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


class TestFtpMissingDependency(unittest.TestCase):
    def test_sftp_connect_raises_import_error_without_pysftp(self):
        ftp = reload_without_deps("luigi.contrib.ftp", "pysftp")
        fs = ftp.RemoteFileSystem("host", sftp=True)
        with self.assertRaises(ImportError) as cm:
            fs._sftp_connect()
        self.assertIn("pysftp", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
